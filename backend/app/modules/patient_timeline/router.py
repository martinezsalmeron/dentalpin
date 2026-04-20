"""Timeline HTTP surface — ``/api/v1/patient_timeline/*``."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import ClinicContext, get_clinic_context, require_permission
from app.core.schemas import ApiResponse
from app.database import get_db
from app.modules.patients.service import PatientService

from .schemas import TimelineResponse
from .service import TimelineService

router = APIRouter()


@router.get(
    "/patients/{patient_id}",
    response_model=ApiResponse[TimelineResponse],
)
async def get_patient_timeline(
    patient_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("patient_timeline.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    category: str | None = Query(default=None, max_length=30),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[TimelineResponse]:
    """Paginated timeline for a patient, optionally filtered by category."""
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
