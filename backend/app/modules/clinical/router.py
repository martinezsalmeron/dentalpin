"""Clinical module router — clinic metadata endpoints only.

All domain routes moved out in Fase B:
- Patient endpoints → patients module (B.1)
- Appointments + cabinets → agenda module (B.2)
- Timeline → patient_timeline module (B.3)

Remaining surface: /clinics GET (list + detail) + PUT for admin
updates.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import ClinicContext, get_clinic_context, require_permission
from app.core.schemas import ApiResponse, PaginatedApiResponse
from app.database import get_db

from .schemas import ClinicResponse, ClinicUpdate

router = APIRouter()


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
