"""FastAPI router for clinical module."""
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import ClinicContext, get_clinic_context
from app.database import get_db
from .schemas import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentUpdate,
    ClinicResponse,
    PaginatedResponse,
    PatientCreate,
    PatientResponse,
    PatientUpdate,
)
from .service import AppointmentService, PatientService

router = APIRouter()


# Patient endpoints
@router.get("/patients", response_model=PaginatedResponse[PatientResponse])
async def list_patients(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
    search: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> PaginatedResponse[PatientResponse]:
    """List patients with optional search."""
    patients, total = await PatientService.list_patients(
        db, ctx.clinic_id, search, page, page_size
    )
    return PaginatedResponse(
        data=[PatientResponse.model_validate(p) for p in patients],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/patients", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    data: PatientCreate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PatientResponse:
    """Create a new patient."""
    patient = await PatientService.create_patient(
        db, ctx.clinic_id, data.model_dump(exclude_unset=True)
    )
    return PatientResponse.model_validate(patient)


@router.get("/patients/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PatientResponse:
    """Get a patient by ID."""
    patient = await PatientService.get_patient(db, ctx.clinic_id, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    return PatientResponse.model_validate(patient)


@router.put("/patients/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: UUID,
    data: PatientUpdate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PatientResponse:
    """Update a patient."""
    patient = await PatientService.get_patient(db, ctx.clinic_id, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    patient = await PatientService.update_patient(
        db, patient, data.model_dump(exclude_unset=True)
    )
    return PatientResponse.model_validate(patient)


@router.delete("/patients/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    patient_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
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
@router.get("/appointments", response_model=PaginatedResponse[AppointmentResponse])
async def list_appointments(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    cabinet: str | None = None,
    professional_id: UUID | None = None,
    appointment_status: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
) -> PaginatedResponse[AppointmentResponse]:
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
    return PaginatedResponse(
        data=[AppointmentResponse.model_validate(a) for a in appointments],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/appointments",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_appointment(
    data: AppointmentCreate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AppointmentResponse:
    """Create a new appointment."""
    # Validate patient access if patient_id provided
    if data.patient_id:
        if not await AppointmentService.validate_patient_access(
            db, ctx.clinic_id, data.patient_id
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found",
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

    return AppointmentResponse.model_validate(appointment)


@router.get("/appointments/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AppointmentResponse:
    """Get an appointment by ID."""
    appointment = await AppointmentService.get_appointment(
        db, ctx.clinic_id, appointment_id
    )
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )
    return AppointmentResponse.model_validate(appointment)


@router.put("/appointments/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: UUID,
    data: AppointmentUpdate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AppointmentResponse:
    """Update an appointment."""
    appointment = await AppointmentService.get_appointment(
        db, ctx.clinic_id, appointment_id
    )
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )

    # Validate patient access if changing patient
    if data.patient_id:
        if not await AppointmentService.validate_patient_access(
            db, ctx.clinic_id, data.patient_id
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found",
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

    return AppointmentResponse.model_validate(appointment)


@router.delete("/appointments/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_appointment(
    appointment_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Cancel an appointment."""
    appointment = await AppointmentService.get_appointment(
        db, ctx.clinic_id, appointment_id
    )
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )

    await AppointmentService.cancel_appointment(db, appointment)


# Clinic endpoints
@router.get("/clinics", response_model=list[ClinicResponse])
async def list_clinics(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
) -> list[ClinicResponse]:
    """List user's clinics (currently returns only the active clinic)."""
    return [ClinicResponse.model_validate(ctx.clinic)]


@router.get("/clinics/{clinic_id}", response_model=ClinicResponse)
async def get_clinic(
    clinic_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
) -> ClinicResponse:
    """Get clinic details."""
    if ctx.clinic_id != clinic_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this clinic",
        )
    return ClinicResponse.model_validate(ctx.clinic)
