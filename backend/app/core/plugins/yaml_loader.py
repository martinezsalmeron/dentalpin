"""Declarative seed-data loader.

Each seed file under a module's ``data/`` folder is a YAML list of
entries. One entry creates or updates a single record owned by the
module and tracked via an ``xml_id`` in ``core_external_id``.

File format::

    - xml_id: billing.tax_iva_21
      table: billing_tax
      noupdate: false
      values:
        name: "IVA 21%"
        rate: 21.00

Cross-record references are supported: any string value of the form
``$xmlref:<xml_id>`` inside ``values`` is resolved post-pass to the
UUID of the referenced record. That record must either be defined
earlier in the same loader run or already exist in
``core_external_id`` (possibly from a previous load of the module).

The loader is intentionally simple: no Jinja, no computed values, no
conditional logic. Complex provisioning belongs in the module's
:meth:`BaseModule.install` hook.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import yaml
from sqlalchemy import MetaData, Table, insert, update
from sqlalchemy.ext.asyncio import AsyncSession

from .external_id import ExternalIdHelper

logger = logging.getLogger(__name__)

_XMLREF_PREFIX = "$xmlref:"


@dataclass
class SeedEntry:
    """A single parsed entry from a YAML seed file."""

    xml_id: str
    table: str
    values: dict[str, Any]
    noupdate: bool = False


class SeedFileError(ValueError):
    """Raised for malformed YAML seed files."""


class UnresolvedReferenceError(ValueError):
    """Raised when an ``$xmlref:`` points to an unknown xml_id."""


def parse_seed_file(path: Path) -> list[SeedEntry]:
    """Read a YAML file and return the list of :class:`SeedEntry`."""
    raw = yaml.safe_load(path.read_text())
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise SeedFileError(f"{path}: expected a list at top level")

    entries: list[SeedEntry] = []
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            raise SeedFileError(f"{path}#{idx}: entry must be a mapping")
        for key in ("xml_id", "table", "values"):
            if key not in item:
                raise SeedFileError(f"{path}#{idx}: missing '{key}'")
        entries.append(
            SeedEntry(
                xml_id=str(item["xml_id"]),
                table=str(item["table"]),
                values=dict(item["values"] or {}),
                noupdate=bool(item.get("noupdate", False)),
            )
        )
    return entries


class SeedLoader:
    """Apply a list of :class:`SeedEntry` to the database idempotently.

    Works against arbitrary table names via SQLAlchemy reflection. The
    caller provides the async session; the loader does not commit —
    the surrounding unit of work (typically the lifespan processor)
    decides when to persist.
    """

    def __init__(self, db: AsyncSession, module_name: str) -> None:
        self.db = db
        self.module_name = module_name
        self._helper = ExternalIdHelper(db)
        self._metadata = MetaData()
        self._resolved_ids: dict[str, UUID] = {}

    async def load(self, entries: list[SeedEntry]) -> dict[str, UUID]:
        """Apply ``entries`` in order and return ``xml_id -> record_id``.

        Running twice with the same entries is a no-op (respecting
        ``noupdate``): records are upserted by xml_id, and
        ``core_external_id`` rows are refreshed.
        """
        # Pre-load already-known xml_ids for this module so cross-refs
        # can resolve against records seeded in earlier runs.
        for ref in await self._helper.list_for_module(self.module_name):
            self._resolved_ids[ref.xml_id] = ref.record_id

        for entry in entries:
            record_id = await self._apply_entry(entry)
            self._resolved_ids[entry.xml_id] = record_id

        return dict(self._resolved_ids)

    # --- Internal -------------------------------------------------------

    async def _apply_entry(self, entry: SeedEntry) -> UUID:
        table = await self._reflect_table(entry.table)
        existing_ref = await self._helper.get(self.module_name, entry.xml_id)
        values = self._resolve_values(entry.values)

        if existing_ref is None:
            record_id = values.get("id")
            if not isinstance(record_id, UUID):
                record_id = uuid4()
                values["id"] = record_id

            await self.db.execute(insert(table).values(**values))
            await self._helper.upsert(
                module_name=self.module_name,
                xml_id=entry.xml_id,
                table_name=entry.table,
                record_id=record_id,
                noupdate=entry.noupdate,
            )
            logger.info(
                "Seeded %s.%s (table=%s, id=%s)",
                self.module_name,
                entry.xml_id,
                entry.table,
                record_id,
            )
            return record_id

        record_id = existing_ref.record_id
        if existing_ref.noupdate:
            logger.debug(
                "Skipping update for noupdate xml_id %s.%s",
                self.module_name,
                entry.xml_id,
            )
        else:
            id_col = self._primary_key_column(table)
            non_id = {k: v for k, v in values.items() if k != id_col.name}
            if non_id:
                await self.db.execute(update(table).where(id_col == record_id).values(**non_id))
            # Refresh the external-id pointer so noupdate flag stays in sync.
            await self._helper.upsert(
                module_name=self.module_name,
                xml_id=entry.xml_id,
                table_name=entry.table,
                record_id=record_id,
                noupdate=entry.noupdate,
            )
        return record_id

    def _resolve_values(self, values: dict[str, Any]) -> dict[str, Any]:
        resolved: dict[str, Any] = {}
        for key, raw in values.items():
            if isinstance(raw, str) and raw.startswith(_XMLREF_PREFIX):
                ref = raw[len(_XMLREF_PREFIX) :]
                if ref not in self._resolved_ids:
                    raise UnresolvedReferenceError(
                        f"xml_id reference not found: {ref} (needed by key {key})"
                    )
                resolved[key] = self._resolved_ids[ref]
            else:
                resolved[key] = raw
        return resolved

    async def _reflect_table(self, name: str) -> Table:
        if name in self._metadata.tables:
            return self._metadata.tables[name]
        conn = await self.db.connection()
        await conn.run_sync(self._metadata.reflect, only=[name])
        if name not in self._metadata.tables:
            raise SeedFileError(f"Table '{name}' not present in database; cannot seed.")
        return self._metadata.tables[name]

    @staticmethod
    def _primary_key_column(table: Table):
        pk = list(table.primary_key.columns)
        if len(pk) != 1:
            raise SeedFileError(
                f"Seed loader needs single-column PK on {table.name}; found {len(pk)}"
            )
        return pk[0]


async def load_module_data_files(
    db: AsyncSession, module_name: str, files: list[Path]
) -> dict[str, UUID]:
    """Convenience entry point used by the install/upgrade processor."""
    loader = SeedLoader(db, module_name)
    all_entries: list[SeedEntry] = []
    for path in files:
        all_entries.extend(parse_seed_file(path))
    return await loader.load(all_entries)
