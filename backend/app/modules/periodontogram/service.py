"""Periodontogram service layer.

Snapshot lifecycle (draft → closed, immutable thereafter), per-tooth and
per-site patches, timeline. Indices computation and the odontogram
pre-fill at draft creation land in PR-3.

All public methods filter by ``clinic_id`` (multi-tenancy guarantee per
``CLAUDE.md``). Validation that a snapshot belongs to the clinic /
patient is the responsibility of these methods — the router only checks
permissions and shape.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .constants import PERIO_TEETH, SITE_CODES, SnapshotStatus
from .models import PeriodontogramSite, PeriodontogramSnapshot, PeriodontogramTooth
from .schemas import SitePatch, ToothPatch


class PeriodontogramService:
    """Static service. Async methods, ``clinic_id`` always required."""

    # ----- READ ---------------------------------------------------------

    @staticmethod
    async def list_snapshots(
        db: AsyncSession,
        clinic_id: UUID,
        patient_id: UUID,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[PeriodontogramSnapshot], int]:
        offset = (page - 1) * page_size
        stmt = (
            select(PeriodontogramSnapshot)
            .where(
                PeriodontogramSnapshot.clinic_id == clinic_id,
                PeriodontogramSnapshot.patient_id == patient_id,
            )
            .order_by(PeriodontogramSnapshot.recorded_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        count_stmt = select(func.count(PeriodontogramSnapshot.id)).where(
            PeriodontogramSnapshot.clinic_id == clinic_id,
            PeriodontogramSnapshot.patient_id == patient_id,
        )
        items = (await db.execute(stmt)).scalars().all()
        total = (await db.execute(count_stmt)).scalar_one()
        return list(items), total

    @staticmethod
    async def get_snapshot(
        db: AsyncSession,
        clinic_id: UUID,
        snapshot_id: UUID,
    ) -> PeriodontogramSnapshot:
        stmt = (
            select(PeriodontogramSnapshot)
            .where(
                PeriodontogramSnapshot.id == snapshot_id,
                PeriodontogramSnapshot.clinic_id == clinic_id,
            )
            .options(
                selectinload(PeriodontogramSnapshot.teeth).selectinload(PeriodontogramTooth.sites),
            )
        )
        snap = (await db.execute(stmt)).scalar_one_or_none()
        if snap is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Snapshot not found",
            )
        return snap

    @staticmethod
    async def get_active_draft(
        db: AsyncSession,
        clinic_id: UUID,
        patient_id: UUID,
    ) -> PeriodontogramSnapshot | None:
        stmt = select(PeriodontogramSnapshot).where(
            PeriodontogramSnapshot.clinic_id == clinic_id,
            PeriodontogramSnapshot.patient_id == patient_id,
            PeriodontogramSnapshot.status == SnapshotStatus.DRAFT.value,
        )
        return (await db.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def get_timeline(
        db: AsyncSession,
        clinic_id: UUID,
        patient_id: UUID,
    ) -> list[dict[str, object]]:
        """Closed snapshots only. Each entry: snapshot_id, date, change_count.

        ``change_count`` is the number of sites with any recorded probing
        depth — a useful proxy for "how complete was this exam" when
        rendering the slider.
        """
        site_subq = (
            select(
                PeriodontogramSite.snapshot_id.label("snapshot_id"),
                func.count(PeriodontogramSite.id).label("filled_sites"),
            )
            .where(PeriodontogramSite.probing_depth_mm.isnot(None))
            .group_by(PeriodontogramSite.snapshot_id)
            .subquery()
        )

        stmt = (
            select(
                PeriodontogramSnapshot.id,
                PeriodontogramSnapshot.closed_at,
                func.coalesce(site_subq.c.filled_sites, 0).label("change_count"),
            )
            .outerjoin(site_subq, site_subq.c.snapshot_id == PeriodontogramSnapshot.id)
            .where(
                PeriodontogramSnapshot.clinic_id == clinic_id,
                PeriodontogramSnapshot.patient_id == patient_id,
                PeriodontogramSnapshot.status == SnapshotStatus.CLOSED.value,
            )
            .order_by(PeriodontogramSnapshot.closed_at.asc())
        )

        rows = (await db.execute(stmt)).all()
        return [
            {
                "snapshot_id": row.id,
                "date": row.closed_at.date().isoformat(),
                "change_count": int(row.change_count),
            }
            for row in rows
        ]

    # ----- WRITE --------------------------------------------------------

    @staticmethod
    async def get_or_create_draft(
        db: AsyncSession,
        clinic_id: UUID,
        patient_id: UUID,
        user_id: UUID,
        recorded_at: datetime | None = None,
    ) -> tuple[PeriodontogramSnapshot, bool]:
        """Idempotent. Returns ``(snapshot, created)``.

        On creation, eagerly inserts a ``PeriodontogramTooth`` row per
        FDI permanent tooth with ``is_present=True, is_implant=False``.
        PR-3 will replace those defaults with values read from the
        odontogram via ``OdontogramService``.
        """
        existing = await PeriodontogramService.get_active_draft(db, clinic_id, patient_id)
        if existing is not None:
            return existing, False

        snap = PeriodontogramSnapshot(
            clinic_id=clinic_id,
            patient_id=patient_id,
            status=SnapshotStatus.DRAFT.value,
            recorded_at=recorded_at or datetime.now(UTC),
            recorded_by=user_id,
        )
        db.add(snap)
        try:
            await db.flush()
        except IntegrityError as exc:
            # Lost the race on the partial-unique-index — another draft
            # was created between get_active_draft and flush. Surface as
            # 409 so the client retries.
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Another draft already exists for this patient",
            ) from exc

        for tooth_number in PERIO_TEETH:
            db.add(
                PeriodontogramTooth(
                    snapshot_id=snap.id,
                    tooth_number=tooth_number,
                    is_present=True,
                    is_implant=False,
                )
            )

        await db.flush()
        return snap, True

    @staticmethod
    async def update_tooth(
        db: AsyncSession,
        clinic_id: UUID,
        snapshot_id: UUID,
        tooth_number: int,
        patch: ToothPatch,
    ) -> PeriodontogramTooth:
        snap = await PeriodontogramService.get_snapshot(db, clinic_id, snapshot_id)
        if snap.status == SnapshotStatus.CLOSED.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Snapshot is closed and immutable",
            )

        stmt = select(PeriodontogramTooth).where(
            PeriodontogramTooth.snapshot_id == snapshot_id,
            PeriodontogramTooth.tooth_number == tooth_number,
        )
        tooth = (await db.execute(stmt)).scalar_one_or_none()
        if tooth is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tooth {tooth_number} not part of snapshot",
            )

        data = patch.model_dump(exclude_unset=True)
        for key, value in data.items():
            setattr(tooth, key, value)
        await db.flush()
        return tooth

    @staticmethod
    async def update_site(
        db: AsyncSession,
        clinic_id: UUID,
        snapshot_id: UUID,
        tooth_number: int,
        site_code: str,
        patch: SitePatch,
    ) -> PeriodontogramSite:
        if site_code not in SITE_CODES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid site code: {site_code}",
            )

        snap = await PeriodontogramService.get_snapshot(db, clinic_id, snapshot_id)
        if snap.status == SnapshotStatus.CLOSED.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Snapshot is closed and immutable",
            )

        tooth_stmt = select(PeriodontogramTooth).where(
            PeriodontogramTooth.snapshot_id == snapshot_id,
            PeriodontogramTooth.tooth_number == tooth_number,
        )
        tooth = (await db.execute(tooth_stmt)).scalar_one_or_none()
        if tooth is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tooth {tooth_number} not part of snapshot",
            )

        site_stmt = select(PeriodontogramSite).where(
            PeriodontogramSite.snapshot_id == snapshot_id,
            PeriodontogramSite.tooth_number == tooth_number,
            PeriodontogramSite.site_code == site_code,
        )
        site = (await db.execute(site_stmt)).scalar_one_or_none()

        data = patch.model_dump(exclude_unset=True)
        if site is None:
            site = PeriodontogramSite(
                snapshot_id=snapshot_id,
                tooth_id=tooth.id,
                tooth_number=tooth_number,
                site_code=site_code,
            )
            db.add(site)
        for key, value in data.items():
            setattr(site, key, value)
        await db.flush()
        return site

    @staticmethod
    async def close_snapshot(
        db: AsyncSession,
        clinic_id: UUID,
        snapshot_id: UUID,
        user_id: UUID,
        notes: str | None = None,
    ) -> PeriodontogramSnapshot:
        snap = await PeriodontogramService.get_snapshot(db, clinic_id, snapshot_id)
        if snap.status == SnapshotStatus.CLOSED.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Snapshot is already closed",
            )

        snap.status = SnapshotStatus.CLOSED.value
        snap.closed_at = datetime.now(UTC)
        snap.closed_by = user_id
        if notes is not None:
            snap.notes = notes
        # ``indices`` stays NULL here — PR-3 wires ``compute_indices`` and
        # the ``periodontogram.snapshot.closed`` event publication.
        await db.flush()
        return snap

    @staticmethod
    async def discard_draft(
        db: AsyncSession,
        clinic_id: UUID,
        snapshot_id: UUID,
    ) -> None:
        snap = await PeriodontogramService.get_snapshot(db, clinic_id, snapshot_id)
        if snap.status != SnapshotStatus.DRAFT.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only draft snapshots can be discarded",
            )
        await db.delete(snap)
        await db.flush()
