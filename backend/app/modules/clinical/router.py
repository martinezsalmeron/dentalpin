"""FastAPI router for clinical module."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import ClinicContext, get_clinic_context, require_permission
from app.core.schemas import ApiResponse, PaginatedApiResponse
from app.database import get_db

from .schemas import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentUpdate,
    CabinetCreate,
    CabinetResponse,
    CabinetUpdate,
    ClinicResponse,
    ClinicUpdate,
    PatientCreate,
    PatientResponse,
    PatientUpdate,
)
from .service import AppointmentService, PatientService

router = APIRouter()


# Patient endpoints
@router.get("/patients", response_model=PaginatedApiResponse[PatientResponse])
async def list_patients(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("clinical.patients.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    search: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> PaginatedApiResponse[PatientResponse]:
    """List patients with optional search."""
    patients, total = await PatientService.list_patients(db, ctx.clinic_id, search, page, page_size)
    return PaginatedApiResponse(
        data=[PatientResponse.model_validate(p) for p in patients],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/patients", response_model=ApiResponse[PatientResponse], status_code=status.HTTP_201_CREATED)
async def create_patient(
    data: PatientCreate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("clinical.patients.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[PatientResponse]:
    """Create a new patient."""
    patient = await PatientService.create_patient(
        db, ctx.clinic_id, data.model_dump(exclude_unset=True)
    )
    return ApiResponse(data=PatientResponse.model_validate(patient))


@router.get("/patients/{patient_id}", response_model=ApiResponse[PatientResponse])
async def get_patient(
    patient_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("clinical.patients.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[PatientResponse]:
    """Get a patient by ID."""
    patient = await PatientService.get_patient(db, ctx.clinic_id, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    return ApiResponse(data=PatientResponse.model_validate(patient))


@router.put("/patients/{patient_id}", response_model=ApiResponse[PatientResponse])
async def update_patient(
    patient_id: UUID,
    data: PatientUpdate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("clinical.patients.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[PatientResponse]:
    """Update a patient."""
    patient = await PatientService.get_patient(db, ctx.clinic_id, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    patient = await PatientService.update_patient(db, patient, data.model_dump(exclude_unset=True))
    return ApiResponse(data=PatientResponse.model_validate(patient))


@router.delete("/patients/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    patient_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("clinical.patients.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Soft delete (archive) a patient."""
    patient = await PatientService.get_patient(db, ctx.clinic_id, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    await PatientService.archive_patient(db, patient)


# Appointment endpoints
@router.get("/appointments", response_model=PaginatedApiResponse[AppointmentResponse])
async def list_appointments(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("clinical.appointments.read"))],
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
    _: Annotated[None, Depends(require_permission("clinical.appointments.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[AppointmentResponse]:
    """Create a new appointment."""
    # Validate patient access if patient_id provided
    if data.patient_id:
        if not await AppointmentService.validate_patient_access(db, ctx.clinic_id, data.patient_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found",
            )

    # Validate professional access
    if not await AppointmentService.validate_professional_access(
        db, ctx.clinic_id, data.professional_id
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid professional: must be a dentist or hygienist in this clinic",
        )

    try:
        appointment = await AppointmentService.create_appointment(
            db, ctx.clinic_id, data.model_dump(exclude_unset=True)
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Time slot is already occupied",
        )

    return ApiResponse(data=AppointmentResponse.model_validate(appointment))


@router.get("/appointments/{appointment_id}", response_model=ApiResponse[AppointmentResponse])
async def get_appointment(
    appointment_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("clinical.appointments.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[AppointmentResponse]:
    """Get an appointment by ID."""
    appointment = await AppointmentService.get_appointment(db, ctx.clinic_id, appointment_id)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )
    return ApiResponse(data=AppointmentResponse.model_validate(appointment))


@router.put("/appointments/{appointment_id}", response_model=ApiResponse[AppointmentResponse])
async def update_appointment(
    appointment_id: UUID,
    data: AppointmentUpdate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("clinical.appointments.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[AppointmentResponse]:
    """Update an appointment."""
    appointment = await AppointmentService.get_appointment(db, ctx.clinic_id, appointment_id)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )

    # Validate patient access if changing patient
    if data.patient_id:
        if not await AppointmentService.validate_patient_access(db, ctx.clinic_id, data.patient_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found",
            )

    # Validate professional access if changing professional
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
            db, appointment, data.model_dump(exclude_unset=True)
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Time slot is already occupied",
        )

    return ApiResponse(data=AppointmentResponse.model_validate(appointment))


@router.delete("/appointments/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_appointment(
    appointment_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("clinical.appointments.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Cancel an appointment."""
    appointment = await AppointmentService.get_appointment(db, ctx.clinic_id, appointment_id)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )

    await AppointmentService.cancel_appointment(db, appointment)


# Clinic endpoints
@router.get("/clinics", response_model=PaginatedApiResponse[ClinicResponse])
async def list_clinics(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
) -> PaginatedApiResponse[ClinicResponse]:
    """List user's clinics (currently returns only the active clinic)."""
    clinics = [ClinicResponse.model_validate(ctx.clinic)]
    return PaginatedApiResponse(
        data=clinics,
        total=len(clinics),
        page=1,
        page_size=len(clinics),
    )


@router.get("/clinics/{clinic_id}", response_model=ApiResponse[ClinicResponse])
async def get_clinic(
    clinic_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
) -> ApiResponse[ClinicResponse]:
    """Get clinic details."""
    if ctx.clinic_id != clinic_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this clinic",
        )
    return ApiResponse(data=ClinicResponse.model_validate(ctx.clinic))


@router.put("/clinics", response_model=ApiResponse[ClinicResponse])
async def update_clinic(
    data: ClinicUpdate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("admin.clinic.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[ClinicResponse]:
    """Update clinic info (admin only)."""
    clinic = ctx.clinic

    if data.name is not None:
        clinic.name = data.name

    await db.commit()
    await db.refresh(clinic)

    return ApiResponse(data=ClinicResponse.model_validate(clinic))


# Cabinet endpoints
@router.post("/cabinets", response_model=ApiResponse[CabinetResponse], status_code=status.HTTP_201_CREATED)
async def create_cabinet(
    data: CabinetCreate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("admin.clinic.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[CabinetResponse]:
    """Create a new cabinet in the clinic."""
    clinic = ctx.clinic
    cabinets = list(clinic.cabinets) if clinic.cabinets else []

    # Check if cabinet name already exists
    if any(c.get("name") == data.name for c in cabinets):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cabinet name already exists",
        )

    new_cabinet = {"name": data.name, "color": data.color}
    cabinets.append(new_cabinet)
    clinic.cabinets = cabinets
    await db.commit()
    await db.refresh(clinic)

    return ApiResponse(data=CabinetResponse(**new_cabinet))


@router.put("/cabinets/{cabinet_name}", response_model=ApiResponse[CabinetResponse])
async def update_cabinet(
    cabinet_name: str,
    data: CabinetUpdate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("admin.clinic.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[CabinetResponse]:
    """Update a cabinet in the clinic."""
    clinic = ctx.clinic
    cabinets = list(clinic.cabinets) if clinic.cabinets else []

    # Find the cabinet
    cabinet_index = None
    for i, c in enumerate(cabinets):
        if c.get("name") == cabinet_name:
            cabinet_index = i
            break

    if cabinet_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cabinet not found",
        )

    # Check if new name already exists (if changing name)
    if data.name and data.name != cabinet_name:
        if any(c.get("name") == data.name for c in cabinets):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cabinet name already exists",
            )

    # Update cabinet
    if data.name:
        cabinets[cabinet_index]["name"] = data.name
    if data.color:
        cabinets[cabinet_index]["color"] = data.color

    clinic.cabinets = cabinets
    await db.commit()
    await db.refresh(clinic)

    return ApiResponse(data=CabinetResponse(**cabinets[cabinet_index]))


@router.delete("/cabinets/{cabinet_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cabinet(
    cabinet_name: str,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("admin.clinic.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a cabinet from the clinic."""
    clinic = ctx.clinic
    cabinets = list(clinic.cabinets) if clinic.cabinets else []

    # Find and remove the cabinet
    original_length = len(cabinets)
    cabinets = [c for c in cabinets if c.get("name") != cabinet_name]

    if len(cabinets) == original_length:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cabinet not found",
        )

    clinic.cabinets = cabinets
    await db.commit()
