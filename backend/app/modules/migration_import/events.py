"""Event publishers + internal progress handler.

External (cross-module) events are published via :func:`publish_*`
helpers from the service layer so consumers reading
``docs/technical/migration_import/events.md`` find a single source of
truth.

The internal ``migration.entity.persisted`` event is used by the
mapper runner to bump :attr:`ImportJob.processed_entities` without
holding the orchestrator state across mapper boundaries.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import update

from app.core.events import event_bus
from app.core.events.types import EventType
from app.database import async_session_maker

from .models import ImportJob

logger = logging.getLogger(__name__)


def publish_job_started(job_id: UUID, clinic_id: UUID) -> None:
    event_bus.publish(
        EventType.MIGRATION_JOB_STARTED,
        {"job_id": str(job_id), "clinic_id": str(clinic_id)},
    )


def publish_job_completed(
    job_id: UUID, clinic_id: UUID, total_entities: int, warnings_count: int
) -> None:
    event_bus.publish(
        EventType.MIGRATION_JOB_COMPLETED,
        {
            "job_id": str(job_id),
            "clinic_id": str(clinic_id),
            "total_entities": total_entities,
            "warnings_count": warnings_count,
        },
    )


def publish_job_failed(job_id: UUID, clinic_id: UUID, error: str) -> None:
    event_bus.publish(
        EventType.MIGRATION_JOB_FAILED,
        {"job_id": str(job_id), "clinic_id": str(clinic_id), "error": error},
    )


def publish_binary_resolved(job_id: UUID, staging_id: UUID, document_id: UUID) -> None:
    event_bus.publish(
        EventType.MIGRATION_BINARY_RESOLVED,
        {
            "job_id": str(job_id),
            "staging_id": str(staging_id),
            "document_id": str(document_id),
        },
    )


def publish_entity_persisted(job_id: UUID, entity_type: str, count: int = 1) -> None:
    event_bus.publish(
        "migration.entity.persisted",
        {"job_id": str(job_id), "entity_type": entity_type, "count": count},
    )


async def on_appointment_created_for_progress(data: dict[str, Any]) -> None:
    """Increment ``processed_entities`` on each persisted entity.

    Runs in a fresh session because the mapper's session is mid-tx.
    The +1 update is a relaxed counter, not a strict invariant —
    progress is for UI feedback only, the source of truth for "what
    got created" is the ``entity_mappings`` table.
    """
    job_id_raw = data.get("job_id")
    count = int(data.get("count", 1))
    if not job_id_raw:
        return
    try:
        job_id = UUID(job_id_raw)
    except (ValueError, TypeError):
        return
    async with async_session_maker() as session:
        await session.execute(
            update(ImportJob)
            .where(ImportJob.id == job_id)
            .values(processed_entities=ImportJob.processed_entities + count)
        )
        await session.commit()
