"""Clinical module router — remaining surface during Fase B.

Appointment + cabinet endpoints moved to the agenda module
(``/api/v1/agenda/*``) in B.2 chunk 1. Patient endpoints moved to the
patients module in B.1. This router still hosts:

* ``GET /api/v1/clinical/patients/{id}/timeline`` — extracted in
  Etapa B.3 into the ``patient_timeline`` module.
* Clinic metadata endpoints (``/clinics``, ``PUT /clinics``) —
  admin surface that stays in clinical until a dedicated home emerges.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import ClinicContext, get_clinic_context, require_permission
from app.core.schemas import ApiResponse, PaginatedApiResponse
from app.database import get_db
from app.modules.patients.service import PatientService

from .schemas import ClinicResponse, ClinicUpdate, TimelineResponse
from .service import TimelineService

router = APIRouter()


# --- Patient timeline --------------------------------------------------


@router.get("/patients/{patient_id}/timeline", response_model=ApiResponse[TimelineResponse])
async def get_patient_timeline(
    patient_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("patients.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    category: str | None = Query(default=None, max_length=30),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[TimelineResponse]:
    """Get patient timeline with optional category filter."""
    patient = await PatientService.get_patient(db, ctx.clinic_id, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    entries, total = await TimelineService.get_timeline(
        db, ctx.clinic_id, patient_id, category, page, page_size
    )

    has_more = (page * page_size) < total
    return ApiResponse(
        data=TimelineResponse(
            entries=entries,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more,
        )
    )


# --- Clinic metadata ---------------------------------------------------


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
    if data.tax_id is not None:
        clinic.tax_id = data.tax_id
    if data.phone is not None:
        clinic.phone = data.phone
    if data.email is not None:
        clinic.email = data.email
    if data.address is not None:
        existing_address = clinic.address or {}
        new_address = data.address.model_dump(exclude_unset=True)
        clinic.address = {**existing_address, **new_address}

    await db.commit()
    await db.refresh(clinic)

    return ApiResponse(data=ClinicResponse.model_validate(clinic))
