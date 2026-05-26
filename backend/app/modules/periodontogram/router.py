"""Periodontogram FastAPI router.

Mounted at ``/api/v1/periodontogram/`` by the module loader.

PR-2 wires the full snapshot lifecycle (list, timeline, draft create/get,
per-tooth and per-site patch, close, discard) plus snapshot detail. The
``/snapshots/{id}/indices`` endpoint and the
``periodontogram.snapshot.closed`` event publication land in PR-3.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import ClinicContext, get_clinic_context, require_permission
from app.core.schemas import ApiResponse, PaginatedApiResponse
from app.database import get_db
from app.modules.patients.models import Patient

from .schemas import (
    IndicesResponse,
    SitePatch,
    SiteValue,
    SnapshotDetail,
    SnapshotSummary,
    TimelineEntry,
    TimelineResponse,
    ToothPatch,
    ToothValue,
)
from .service import PeriodontogramService

router = APIRouter()


async def _ensure_patient(db: AsyncSession, clinic_id: UUID, patient_id: UUID) -> None:
    """Mirror the odontogram pattern: 404 if patient is missing/archived."""
    stmt = select(Patient).where(
        Patient.id == patient_id,
        Patient.clinic_id == clinic_id,
        Patient.status != "archived",
    )
    if (await db.execute(stmt)).scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")


def _serialise_snapshot(snap) -> SnapshotDetail:
    teeth = sorted(snap.teeth, key=lambda t: t.tooth_number)
    teeth_values: list[ToothValue] = []
    for tooth in teeth:
        sites = sorted(tooth.sites, key=lambda s: s.site_code)
        teeth_values.append(
            ToothValue(
                tooth_number=tooth.tooth_number,
                is_present=tooth.is_present,
                is_implant=tooth.is_implant,
                mobility=tooth.mobility,
                prognosis=tooth.prognosis,
                furcation_buccal=tooth.furcation_buccal,
                furcation_lingual=tooth.furcation_lingual,
                keratinized_gingiva_mm=tooth.keratinized_gingiva_mm,
                sites=[SiteValue.model_validate(s) for s in sites],
            )
        )
    return SnapshotDetail(
        id=snap.id,
        patient_id=snap.patient_id,
        status=snap.status,
        recorded_at=snap.recorded_at,
        recorded_by=snap.recorded_by,
        closed_at=snap.closed_at,
        closed_by=snap.closed_by,
        notes=snap.notes,
        indices=IndicesResponse(**snap.indices) if snap.indices else None,
        teeth=teeth_values,
    )


# ---------------------------------------------------------------------------
# Patient-scoped endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/patients/{patient_id}/snapshots",
    response_model=PaginatedApiResponse[SnapshotSummary],
)
async def list_patient_snapshots(
    patient_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("periodontogram.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
) -> PaginatedApiResponse[SnapshotSummary]:
    await _ensure_patient(db, ctx.clinic_id, patient_id)
    items, total = await PeriodontogramService.list_snapshots(
        db, ctx.clinic_id, patient_id, page, page_size
    )
    return PaginatedApiResponse(
        data=[SnapshotSummary.model_validate(s) for s in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/patients/{patient_id}/timeline",
    response_model=ApiResponse[TimelineResponse],
)
async def get_patient_timeline(
    patient_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("periodontogram.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[TimelineResponse]:
    await _ensure_patient(db, ctx.clinic_id, patient_id)
    rows = await PeriodontogramService.get_timeline(db, ctx.clinic_id, patient_id)
    draft = await PeriodontogramService.get_active_draft(db, ctx.clinic_id, patient_id)
    return ApiResponse(
        data=TimelineResponse(
            dates=[TimelineEntry(**row) for row in rows],
            draft=SnapshotSummary.model_validate(draft) if draft else None,
        )
    )


@router.get(
    "/patients/{patient_id}/draft",
    response_model=ApiResponse[SnapshotDetail | None],
)
async def get_patient_draft(
    patient_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("periodontogram.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[SnapshotDetail | None]:
    await _ensure_patient(db, ctx.clinic_id, patient_id)
    draft = await PeriodontogramService.get_active_draft(db, ctx.clinic_id, patient_id)
    if draft is None:
        return ApiResponse(data=None)
    snap = await PeriodontogramService.get_snapshot(db, ctx.clinic_id, draft.id)
    return ApiResponse(data=_serialise_snapshot(snap))


@router.post(
    "/patients/{patient_id}/draft",
    response_model=ApiResponse[SnapshotDetail],
)
async def open_patient_draft(
    patient_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("periodontogram.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[SnapshotDetail]:
    await _ensure_patient(db, ctx.clinic_id, patient_id)
    snap, _created = await PeriodontogramService.get_or_create_draft(
        db, ctx.clinic_id, patient_id, ctx.user_id
    )
    await db.commit()
    # Reload eagerly with teeth + sites for serialisation.
    detail = await PeriodontogramService.get_snapshot(db, ctx.clinic_id, snap.id)
    return ApiResponse(data=_serialise_snapshot(detail))


# ---------------------------------------------------------------------------
# Snapshot-scoped endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/snapshots/{snapshot_id}",
    response_model=ApiResponse[SnapshotDetail],
)
async def get_snapshot_detail(
    snapshot_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("periodontogram.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[SnapshotDetail]:
    snap = await PeriodontogramService.get_snapshot(db, ctx.clinic_id, snapshot_id)
    return ApiResponse(data=_serialise_snapshot(snap))


@router.patch(
    "/snapshots/{snapshot_id}/teeth/{tooth_number}",
    response_model=ApiResponse[ToothValue],
)
async def patch_snapshot_tooth(
    snapshot_id: UUID,
    tooth_number: int,
    patch: ToothPatch,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("periodontogram.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[ToothValue]:
    tooth = await PeriodontogramService.update_tooth(
        db, ctx.clinic_id, snapshot_id, tooth_number, patch
    )
    await db.commit()
    return ApiResponse(
        data=ToothValue(
            tooth_number=tooth.tooth_number,
            is_present=tooth.is_present,
            is_implant=tooth.is_implant,
            mobility=tooth.mobility,
            prognosis=tooth.prognosis,
            furcation_buccal=tooth.furcation_buccal,
            furcation_lingual=tooth.furcation_lingual,
            keratinized_gingiva_mm=tooth.keratinized_gingiva_mm,
            sites=[],
        )
    )


@router.patch(
    "/snapshots/{snapshot_id}/teeth/{tooth_number}/sites/{site_code}",
    response_model=ApiResponse[SiteValue],
)
async def patch_snapshot_site(
    snapshot_id: UUID,
    tooth_number: int,
    site_code: str,
    patch: SitePatch,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("periodontogram.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[SiteValue]:
    site = await PeriodontogramService.update_site(
        db, ctx.clinic_id, snapshot_id, tooth_number, site_code, patch
    )
    await db.commit()
    return ApiResponse(data=SiteValue.model_validate(site))


class _CloseBody(BaseModel):
    notes: str | None = None


@router.post(
    "/snapshots/{snapshot_id}/close",
    response_model=ApiResponse[SnapshotDetail],
)
async def close_snapshot(
    snapshot_id: UUID,
    body: _CloseBody,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("periodontogram.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[SnapshotDetail]:
    await PeriodontogramService.close_snapshot(
        db, ctx.clinic_id, snapshot_id, ctx.user_id, body.notes
    )
    await db.commit()
    detail = await PeriodontogramService.get_snapshot(db, ctx.clinic_id, snapshot_id)
    return ApiResponse(data=_serialise_snapshot(detail))


@router.get(
    "/snapshots/{snapshot_id}/indices",
    response_model=ApiResponse[IndicesResponse],
)
async def get_snapshot_indices(
    snapshot_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("periodontogram.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[IndicesResponse]:
    """Return frozen indices on closed snapshots or live-computed indices
    on drafts. Lets the UI render the same banner regardless of state."""
    from .indices import compute_indices

    snap = await PeriodontogramService.get_snapshot(db, ctx.clinic_id, snapshot_id)
    if snap.indices:
        return ApiResponse(data=IndicesResponse(**snap.indices))
    live = compute_indices(snap.teeth)
    return ApiResponse(data=IndicesResponse(**live))


@router.delete(
    "/snapshots/{snapshot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def discard_snapshot(
    snapshot_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("periodontogram.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    await PeriodontogramService.discard_draft(db, ctx.clinic_id, snapshot_id)
    await db.commit()
