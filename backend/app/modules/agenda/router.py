"""Agenda HTTP surface: appointments + cabinets.

Mounts at ``/api/v1/agenda/*``. Appointments use the
``agenda.appointments.*`` namespace; cabinets still gate on
``admin.clinic.write`` until Etapa B.2 chunk 3 normalizes cabinets
into their own table + permission namespace.
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import ClinicContext, get_clinic_context, require_permission
from app.core.schemas import ApiResponse, PaginatedApiResponse
from app.database import get_db

from .models import Appointment
from .schemas import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentStatusEventResponse,
    AppointmentStatusTransition,
    AppointmentUpdate,
    CabinetCreate,
    CabinetResponse,
    CabinetUpdate,
)
from .service import (
    AlreadyInStateError,
    AppointmentService,
    CabinetService,
    InvalidTransitionError,
)

router = APIRouter()


# --- Appointments -------------------------------------------------------


@router.get("/appointments", response_model=PaginatedApiResponse[AppointmentResponse])
async def list_appointments(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("agenda.appointments.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    cabinet: str | None = None,
    professional_id: UUID | None = None,
    appointment_status: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
) -> PaginatedApiResponse[AppointmentResponse]:
    """List appointments with filters."""
    appointments, total = await AppointmentService.list_appointments(
        db,
        ctx.clinic_id,
        start_date,
        end_date,
        cabinet,
        professional_id,
        appointment_status,
        page,
        page_size,
    )
    return PaginatedApiResponse(
        data=[AppointmentResponse.model_validate(a) for a in appointments],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/appointments",
    response_model=ApiResponse[AppointmentResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_appointment(
    data: AppointmentCreate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("agenda.appointments.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[AppointmentResponse]:
    """Create a new appointment."""
    if data.patient_id:
        if not await AppointmentService.validate_patient_access(db, ctx.clinic_id, data.patient_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found",
            )

    if not await AppointmentService.validate_professional_access(
        db, ctx.clinic_id, data.professional_id
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid professional: must be a dentist or hygienist in this clinic",
        )

    try:
        appointment = await AppointmentService.create_appointment(
            db,
            ctx.clinic_id,
            data.model_dump(exclude_unset=True),
            created_by=ctx.user_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Time slot is already occupied",
        ) from e

    return ApiResponse(data=AppointmentResponse.model_validate(appointment))


@router.get("/appointments/{appointment_id}", response_model=ApiResponse[AppointmentResponse])
async def get_appointment(
    appointment_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("agenda.appointments.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[AppointmentResponse]:
    """Get an appointment by ID, including the status audit trail."""
    appointment = await AppointmentService.get_appointment(db, ctx.clinic_id, appointment_id)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )
    events = await AppointmentService.list_status_events(db, ctx.clinic_id, appointment.id)
    response = AppointmentResponse.model_validate(appointment)
    response.history = [AppointmentStatusEventResponse.model_validate(e) for e in events]
    return ApiResponse(data=response)


@router.put("/appointments/{appointment_id}", response_model=ApiResponse[AppointmentResponse])
async def update_appointment(
    appointment_id: UUID,
    data: AppointmentUpdate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("agenda.appointments.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[AppointmentResponse]:
    """Update an appointment."""
    appointment = await AppointmentService.get_appointment(db, ctx.clinic_id, appointment_id)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )

    if data.patient_id:
        if not await AppointmentService.validate_patient_access(db, ctx.clinic_id, data.patient_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found",
            )

    if data.professional_id:
        if not await AppointmentService.validate_professional_access(
            db, ctx.clinic_id, data.professional_id
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid professional: must be a dentist or hygienist in this clinic",
            )

    try:
        appointment = await AppointmentService.update_appointment(
            db,
            appointment,
            data.model_dump(exclude_unset=True),
            changed_by=ctx.user_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Time slot is already occupied",
        ) from e

    return ApiResponse(data=AppointmentResponse.model_validate(appointment))


@router.delete("/appointments/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_appointment(
    appointment_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("agenda.appointments.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Cancel an appointment."""
    appointment = await AppointmentService.get_appointment(db, ctx.clinic_id, appointment_id)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )
    try:
        await AppointmentService.cancel_appointment(db, appointment, changed_by=ctx.user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post(
    "/appointments/{appointment_id}/transitions",
    response_model=ApiResponse[AppointmentResponse],
)
async def transition_appointment(
    appointment_id: UUID,
    data: AppointmentStatusTransition,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("agenda.appointments.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[AppointmentResponse]:
    """Advance (or cancel) an appointment's status.

    Returns the full appointment with its ``history`` populated so the
    frontend can update the detail view in one round-trip.
    """
    appointment = await AppointmentService.get_appointment(db, ctx.clinic_id, appointment_id)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )
    try:
        await AppointmentService.transition(
            db, appointment, data.to_status, changed_by=ctx.user_id, note=data.note
        )
    except AlreadyInStateError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e
    except InvalidTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    events = await AppointmentService.list_status_events(db, ctx.clinic_id, appointment.id)
    response = AppointmentResponse.model_validate(appointment)
    response.history = [AppointmentStatusEventResponse.model_validate(e) for e in events]
    return ApiResponse(data=response)


@router.get(
    "/appointments/{appointment_id}/transitions",
    response_model=ApiResponse[list[AppointmentStatusEventResponse]],
)
async def list_appointment_transitions(
    appointment_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("agenda.appointments.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[list[AppointmentStatusEventResponse]]:
    """Return the full status audit trail for an appointment (asc)."""
    appointment = await AppointmentService.get_appointment(db, ctx.clinic_id, appointment_id)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )
    events = await AppointmentService.list_status_events(db, ctx.clinic_id, appointment.id)
    return ApiResponse(data=[AppointmentStatusEventResponse.model_validate(e) for e in events])


# --- Cabinets (real table) ----------------------------------------------


@router.get("/cabinets", response_model=ApiResponse[list[CabinetResponse]])
async def list_cabinets(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("agenda.cabinets.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[list[CabinetResponse]]:
    """List cabinets in the current clinic."""
    cabinets = await CabinetService.list_cabinets(db, ctx.clinic_id)
    return ApiResponse(data=[CabinetResponse.model_validate(c) for c in cabinets])


@router.post(
    "/cabinets",
    response_model=ApiResponse[CabinetResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_cabinet(
    data: CabinetCreate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("agenda.cabinets.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[CabinetResponse]:
    """Create a new cabinet in the clinic."""
    existing = await CabinetService.get_by_name(db, ctx.clinic_id, data.name)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cabinet name already exists",
        )

    cabinet = await CabinetService.create_cabinet(
        db, ctx.clinic_id, data.model_dump(exclude_unset=True)
    )
    await db.commit()
    await db.refresh(cabinet)
    return ApiResponse(data=CabinetResponse.model_validate(cabinet))


@router.put("/cabinets/{cabinet_id}", response_model=ApiResponse[CabinetResponse])
async def update_cabinet(
    cabinet_id: UUID,
    data: CabinetUpdate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("agenda.cabinets.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[CabinetResponse]:
    """Update a cabinet."""
    cabinet = await CabinetService.get_cabinet(db, ctx.clinic_id, cabinet_id)
    if cabinet is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cabinet not found",
        )

    if data.name and data.name != cabinet.name:
        clash = await CabinetService.get_by_name(db, ctx.clinic_id, data.name)
        if clash is not None and clash.id != cabinet.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cabinet name already exists",
            )

    cabinet = await CabinetService.update_cabinet(db, cabinet, data.model_dump(exclude_unset=True))
    await db.commit()
    await db.refresh(cabinet)
    return ApiResponse(data=CabinetResponse.model_validate(cabinet))


@router.delete("/cabinets/{cabinet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cabinet(
    cabinet_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("agenda.cabinets.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a cabinet. Blocks when any non-cancelled appointment still uses it."""
    cabinet = await CabinetService.get_cabinet(db, ctx.clinic_id, cabinet_id)
    if cabinet is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cabinet not found",
        )

    from sqlalchemy import func as sql_func

    in_use = (
        await db.execute(
            select(sql_func.count())
            .select_from(Appointment)
            .where(
                Appointment.cabinet_id == cabinet.id,
                Appointment.status != "cancelled",
            )
        )
    ).scalar() or 0
    if in_use:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cabinet has {in_use} active appointments",
        )

    await CabinetService.delete_cabinet(db, cabinet)
    await db.commit()
