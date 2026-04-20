"""TimelineService — queries + inserts for the patient timeline."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import PatientTimeline
from .schemas import TimelineEntry


class TimelineService:
    """Business logic for the patient timeline."""

    @staticmethod
    async def get_timeline(
        db: AsyncSession,
        clinic_id: UUID,
        patient_id: UUID,
        category: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[TimelineEntry], int]:
        """Return paginated timeline entries for a patient."""
        page_size = min(max(page_size, 1), 100)
        page = max(page, 1)
        offset = (page - 1) * page_size

        query = select(PatientTimeline).where(
            PatientTimeline.clinic_id == clinic_id,
            PatientTimeline.patient_id == patient_id,
        )

        if category:
            query = query.where(PatientTimeline.event_category == category)

        total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0

        query = query.order_by(PatientTimeline.occurred_at.desc())
        query = query.offset(offset).limit(page_size)
        result = await db.execute(query)
        entries = result.scalars().all()

        return [TimelineEntry.model_validate(e) for e in entries], total

    @staticmethod
    async def add_entry(
        db: AsyncSession,
        clinic_id: UUID,
        patient_id: UUID,
        event_type: str,
        event_category: str,
        source_table: str,
        source_id: UUID,
        title: str,
        description: str | None = None,
        event_data: dict | None = None,
        occurred_at: datetime | None = None,
        created_by: UUID | None = None,
    ) -> PatientTimeline:
        """Insert a new timeline entry."""
        entry = PatientTimeline(
            clinic_id=clinic_id,
            patient_id=patient_id,
            event_type=event_type,
            event_category=event_category,
            source_table=source_table,
            source_id=source_id,
            title=title,
            description=description,
            event_data=event_data,
            occurred_at=occurred_at or datetime.utcnow(),
            created_by=created_by,
        )
        db.add(entry)
        await db.flush()
        return entry
