"""Idempotent seed record tracking via stable xml_id handles.

Each record a module creates via its ``install`` or ``post_upgrade``
lifecycle hook can be tagged with an ``xml_id`` (e.g.
``billing.tax_iva_21``). The registry stores the pointer in
``core_external_id`` so that:

* **upgrade** — the module can find the existing record by xml_id and
  update fields in place (unless ``noupdate=True``).
* **uninstall** — the registry can list + delete all records owned by
  the module without the module needing to track them.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from .db_models import ExternalId


@dataclass
class ExternalIdRef:
    """Projection of an external id row."""

    module_name: str
    xml_id: str
    table_name: str
    record_id: UUID
    noupdate: bool


class ExternalIdHelper:
    """Thin async service around ``core_external_id``.

    Not a singleton — callers construct one per unit of work with a
    live session.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def upsert(
        self,
        *,
        module_name: str,
        xml_id: str,
        table_name: str,
        record_id: UUID,
        noupdate: bool = False,
    ) -> ExternalIdRef:
        """Create or update the xml_id pointer.

        When a row already exists for (module_name, xml_id), the
        ``table_name`` / ``record_id`` / ``noupdate`` fields are
        refreshed. The database enforces uniqueness on the composite.
        """
        existing = await self._get(module_name, xml_id)
        if existing is None:
            row = ExternalId(
                module_name=module_name,
                xml_id=xml_id,
                table_name=table_name,
                record_id=record_id,
                noupdate=noupdate,
            )
            self.db.add(row)
            await self.db.flush()
        else:
            existing.table_name = table_name
            existing.record_id = record_id
            existing.noupdate = noupdate
            row = existing

        return self._to_ref(row)

    async def get(self, module_name: str, xml_id: str) -> ExternalIdRef | None:
        row = await self._get(module_name, xml_id)
        return self._to_ref(row) if row else None

    async def list_for_module(self, module_name: str) -> list[ExternalIdRef]:
        result = await self.db.execute(
            select(ExternalId).where(ExternalId.module_name == module_name)
        )
        return [self._to_ref(r) for r in result.scalars()]

    async def purge_for_module(self, module_name: str) -> list[tuple[str, UUID]]:
        """Delete every xml_id row owned by ``module_name``.

        Returns the ``(table_name, record_id)`` pairs that used to be
        tracked so callers can delete the underlying rows in the right
        order. Rows are returned in insertion order (oldest first); the
        caller is expected to delete them in reverse to respect FK
        cascade expectations.
        """
        rows = await self.list_for_module(module_name)
        pairs = [(r.table_name, r.record_id) for r in rows]

        await self.db.execute(delete(ExternalId).where(ExternalId.module_name == module_name))
        return pairs

    # --- Internal -------------------------------------------------------

    async def _get(self, module_name: str, xml_id: str) -> ExternalId | None:
        result = await self.db.execute(
            select(ExternalId).where(
                ExternalId.module_name == module_name,
                ExternalId.xml_id == xml_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _to_ref(row: ExternalId) -> ExternalIdRef:
        return ExternalIdRef(
            module_name=row.module_name,
            xml_id=row.xml_id,
            table_name=row.table_name,
            record_id=row.record_id,
            noupdate=row.noupdate,
        )
