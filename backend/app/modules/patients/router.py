"""Patient HTTP surface.

Mounts under ``/api/v1/patients/*``. Permissions live in the
``patients.*`` namespace: ``patients.read``, ``patients.write``,
``patients.medical.read`` and ``patients.medical.write``.
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import ClinicContext, get_clinic_context, require_permission
from app.core.schemas import ApiResponse, PaginatedApiResponse
from app.database import get_db

from .schemas import (
    MedicalHistoryResponse,
    MedicalHistoryUpdate,
    PatientAlertsResponse,
    PatientCreate,
    PatientExtendedResponse,
    PatientExtendedUpdate,
    PatientResponse,
    PatientUpdate,
)
from .service import PatientService

router = APIRouter()


@router.get("/recent", response_model=ApiResponse[list[PatientResponse]])
async def get_recent_patients(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("patients.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=8, ge=1, le=20),
) -> ApiResponse[list[PatientResponse]]:
    """Get recent patients (by last visit or creation date)."""
    patients = await PatientService.get_recent_patients(db, ctx.clinic_id, limit)
    return ApiResponse(data=[PatientResponse.model_validate(p) for p in patients])


@router.get("", response_model=PaginatedApiResponse[PatientResponse])
async def list_patients(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("patients.read"))],
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


@router.post(
    "",
    response_model=ApiResponse[PatientResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_patient(
    data: PatientCreate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("patients.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[PatientResponse]:
    """Create a new patient."""
    patient = await PatientService.create_patient(
        db, ctx.clinic_id, data.model_dump(exclude_unset=True)
    )
    return ApiResponse(data=PatientResponse.model_validate(patient))


@router.get("/{patient_id}", response_model=ApiResponse[PatientResponse])
async def get_patient(
    patient_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("patients.read"))],
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


@router.put("/{patient_id}", response_model=ApiResponse[PatientResponse])
async def update_patient(
    patient_id: UUID,
    data: PatientUpdate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("patients.write"))],
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


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    patient_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("patients.write"))],
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


# --- Extended info ------------------------------------------------------


@router.get("/{patient_id}/extended", response_model=ApiResponse[PatientExtendedResponse])
async def get_patient_extended(
    patient_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("patients.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[PatientExtendedResponse]:
    """Get patient with extended info (demographics, emergency contact, alerts)."""
    patient = await PatientService.get_patient(db, ctx.clinic_id, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    return ApiResponse(data=PatientExtendedResponse.model_validate(patient))


@router.put("/{patient_id}/extended", response_model=ApiResponse[PatientExtendedResponse])
async def update_patient_extended(
    patient_id: UUID,
    data: PatientExtendedUpdate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("patients.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[PatientExtendedResponse]:
    """Update patient with extended fields."""
    patient = await PatientService.get_patient(db, ctx.clinic_id, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    patient = await PatientService.update_patient(db, patient, data.model_dump(exclude_unset=True))
    return ApiResponse(data=PatientExtendedResponse.model_validate(patient))


# --- Medical history ----------------------------------------------------


@router.get(
    "/{patient_id}/medical-history",
    response_model=ApiResponse[MedicalHistoryResponse],
)
async def get_medical_history(
    patient_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("patients.medical.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[MedicalHistoryResponse]:
    """Get patient medical history."""
    patient = await PatientService.get_patient(db, ctx.clinic_id, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    medical_history = patient.medical_history or {}
    return ApiResponse(data=MedicalHistoryResponse.model_validate(medical_history))


@router.put(
    "/{patient_id}/medical-history",
    response_model=ApiResponse[MedicalHistoryResponse],
)
async def update_medical_history(
    patient_id: UUID,
    data: MedicalHistoryUpdate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("patients.medical.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[MedicalHistoryResponse]:
    """Update patient medical history."""
    patient = await PatientService.get_patient(db, ctx.clinic_id, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    medical_data = data.model_dump()
    medical_data["last_updated_at"] = datetime.utcnow().isoformat()
    medical_data["last_updated_by"] = str(ctx.user_id)

    patient = await PatientService.update_medical_history(db, patient, medical_data, ctx.user_id)
    return ApiResponse(data=MedicalHistoryResponse.model_validate(patient.medical_history))


# --- Alerts -------------------------------------------------------------


@router.get("/{patient_id}/alerts", response_model=ApiResponse[PatientAlertsResponse])
async def get_patient_alerts(
    patient_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("patients.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[PatientAlertsResponse]:
    """Get active alerts for a patient (computed from medical history)."""
    patient = await PatientService.get_patient(db, ctx.clinic_id, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    return ApiResponse(data=PatientAlertsResponse(alerts=patient.active_alerts))
