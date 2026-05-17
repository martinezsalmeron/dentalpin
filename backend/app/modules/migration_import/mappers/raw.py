"""Fallback mapper — writes a :class:`RawEntity` row for forward-compat.

Every DPMF entity_type without a dedicated mapper lands here. The
operator does not lose the data; a future module (e.g. ``prescriptions``)
can rehydrate from these rows when it ships.

Idempotency: ``(job_id, entity_type, canonical_uuid)`` is UNIQUE in
``raw_entities``; an ON CONFLICT DO NOTHING insert keeps re-imports
cheap.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.dialects.postgresql import insert as pg_insert

from ..models import RawEntity
from .base import MapperContext


class RawEntityMapper:
    async def apply(
        self,
        ctx: MapperContext,
        *,
        entity_type: str,
        payload: dict[str, Any],
        raw: dict[str, Any],
        canonical_uuid: str,
        source_id: str,
        source_system: str,
    ) -> UUID | None:
        stmt = (
            pg_insert(RawEntity)
            .values(
                id=uuid4(),
                clinic_id=ctx.clinic_id,
                job_id=ctx.job_id,
                entity_type=entity_type,
                canonical_uuid=canonical_uuid,
                source_system=source_system,
                source_id=source_id,
                payload=payload,
                raw_source_data=raw,
            )
            .on_conflict_do_nothing(index_elements=["job_id", "entity_type", "canonical_uuid"])
        )
        await ctx.db.execute(stmt)
        return None
