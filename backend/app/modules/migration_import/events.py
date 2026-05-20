"""Event publishers.

External (cross-module) events are published via :func:`publish_*`
helpers from the service layer so consumers reading
``docs/technical/migration_import/events.md`` find a single source of
truth.

``migration.entity.persisted`` is now emitted once per commit batch
(not once per entity) — see ``service._run_pipeline``. External
modules can subscribe for progress updates; the importer itself no
longer needs to because the counter bump happens inline.
"""

from __future__ import annotations

import logging
from uuid import UUID

from app.core.events import event_bus
from app.core.events.types import EventType

logger = logging.getLogger(__name__)


async def publish_job_started(job_id: UUID, clinic_id: UUID) -> None:
    await event_bus.publish(
        EventType.MIGRATION_JOB_STARTED,
        {"job_id": str(job_id), "clinic_id": str(clinic_id)},
    )


async def publish_job_completed(
    job_id: UUID, clinic_id: UUID, total_entities: int, warnings_count: int
) -> None:
    await event_bus.publish(
        EventType.MIGRATION_JOB_COMPLETED,
        {
            "job_id": str(job_id),
            "clinic_id": str(clinic_id),
            "total_entities": total_entities,
            "warnings_count": warnings_count,
        },
    )


async def publish_job_failed(job_id: UUID, clinic_id: UUID, error: str) -> None:
    await event_bus.publish(
        EventType.MIGRATION_JOB_FAILED,
        {"job_id": str(job_id), "clinic_id": str(clinic_id), "error": error},
    )


async def publish_binary_resolved(job_id: UUID, staging_id: UUID, document_id: UUID) -> None:
    await event_bus.publish(
        EventType.MIGRATION_BINARY_RESOLVED,
        {
            "job_id": str(job_id),
            "staging_id": str(staging_id),
            "document_id": str(document_id),
        },
    )


async def publish_entity_persisted(job_id: UUID, entity_type: str, count: int = 1) -> None:
    await event_bus.publish(
        EventType.MIGRATION_ENTITY_PERSISTED,
        {"job_id": str(job_id), "entity_type": entity_type, "count": count},
    )
