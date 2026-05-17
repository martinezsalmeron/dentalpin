"""Mapper foundations: :class:`MapperContext` and :class:`MappingResolver`.

Both live in a single module so concrete mappers can keep their imports
tight (``from .base import MapperContext, MappingResolver``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import EntityMapping


class MappingResolver:
    """Read / write the ``entity_mappings`` table.

    All FK resolution between DPMF entities goes through this object —
    mappers never use canonical UUIDs directly as DentalPin row IDs.

    Memoisation is per-instance (one resolver per job), bounded by the
    number of distinct entity_type+canonical_uuid pairs in the file.
    """

    def __init__(self, db: AsyncSession, clinic_id: UUID, job_id: UUID) -> None:
        self._db = db
        self._clinic_id = clinic_id
        self._job_id = job_id
        self._cache: dict[tuple[str, str], UUID] = {}

    async def get(self, entity_type: str, canonical_uuid: str) -> UUID | None:
        """Return the DentalPin row id mapped to ``(entity_type, canonical_uuid)``.

        Scoped to ``clinic_id`` so two clinics importing the same DPMF
        do not see each other's resolutions.
        """
        key = (entity_type, canonical_uuid)
        if key in self._cache:
            return self._cache[key]
        result = await self._db.execute(
            select(EntityMapping.dentalpin_id).where(
                EntityMapping.clinic_id == self._clinic_id,
                EntityMapping.entity_type == entity_type,
                EntityMapping.source_canonical_uuid == canonical_uuid,
            )
        )
        row = result.scalar_one_or_none()
        if row is not None:
            self._cache[key] = row
        return row

    async def set(
        self,
        entity_type: str,
        canonical_uuid: str,
        source_system: str,
        dentalpin_table: str,
        dentalpin_id: UUID,
    ) -> None:
        """Persist the mapping. Idempotent — duplicate inserts no-op via
        the UNIQUE constraint."""
        mapping = EntityMapping(
            clinic_id=self._clinic_id,
            job_id=self._job_id,
            source_system=source_system,
            entity_type=entity_type,
            source_canonical_uuid=canonical_uuid,
            dentalpin_table=dentalpin_table,
            dentalpin_id=dentalpin_id,
        )
        self._db.add(mapping)
        self._cache[(entity_type, canonical_uuid)] = dentalpin_id


@dataclass
class MapperContext:
    """Per-job context handed to every mapper invocation."""

    db: AsyncSession
    clinic_id: UUID
    job_id: UUID
    resolver: MappingResolver
    import_fiscal_compliance: bool


class Mapper(Protocol):
    """Structural interface every concrete mapper satisfies."""

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
    ) -> UUID | None: ...
