"""Module service layer.

Thin facade over :class:`ModuleRegistry` + the ``core_module`` tables.
For Etapa 1 this service is read-mostly: it discovers modules, reconciles
the DB, and answers ``list``/``info``/``status``/``doctor`` queries.

Install, uninstall and upgrade flows arrive in Etapa 3.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseModule
from .db_models import ModuleRecord
from .loader import discover_modules
from .manifest import Manifest, ManifestError
from .registry import module_registry
from .state import ModuleCategory, ModuleState

logger = logging.getLogger(__name__)


@dataclass
class ModuleInfo:
    """Projection of a module + its DB row for CLI/API output."""

    name: str
    version: str
    state: ModuleState
    category: ModuleCategory
    removable: bool
    auto_install: bool
    installed_at: datetime | None
    last_state_change: datetime
    base_revision: str | None
    applied_revision: str | None
    error_message: str | None
    error_at: datetime | None
    summary: str
    depends: list[str]
    in_disk: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "state": self.state.value,
            "category": self.category.value,
            "removable": self.removable,
            "auto_install": self.auto_install,
            "installed_at": self.installed_at.isoformat() if self.installed_at else None,
            "last_state_change": self.last_state_change.isoformat(),
            "base_revision": self.base_revision,
            "applied_revision": self.applied_revision,
            "error_message": self.error_message,
            "error_at": self.error_at.isoformat() if self.error_at else None,
            "summary": self.summary,
            "depends": self.depends,
            "in_disk": self.in_disk,
        }


@dataclass
class DoctorReport:
    """Diagnostic output from :meth:`ModuleService.doctor`."""

    orphans: list[str]
    missing_dependencies: list[tuple[str, str]]
    manifest_errors: list[tuple[str, str]]
    errored_modules: list[tuple[str, str]]

    @property
    def ok(self) -> bool:
        return not (
            self.orphans
            or self.missing_dependencies
            or self.manifest_errors
            or self.errored_modules
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "orphans": self.orphans,
            "missing_dependencies": [
                {"module": m, "missing": dep} for m, dep in self.missing_dependencies
            ],
            "manifest_errors": [{"module": m, "error": err} for m, err in self.manifest_errors],
            "errored_modules": [{"module": m, "error": err} for m, err in self.errored_modules],
        }


class ModuleService:
    """Service-layer operations on modules.

    Usage: instantiate per request/CLI invocation with a live session.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # --- Discovery + reconciliation -------------------------------------

    def discovered(self) -> list[BaseModule]:
        """Return modules currently loaded in the in-memory registry."""
        return module_registry.list_modules()

    async def reconcile_with_db(self) -> None:
        """Ensure ``core_module`` contains one row per discovered module.

        For v1 (Etapa 1): discovered modules that are new in the DB are
        inserted as ``installed`` (their routers/handlers are already
        mounted by :func:`load_modules`, so they are effectively live).
        Discovered modules already in the DB have their ``version`` +
        ``manifest_snapshot`` refreshed if the version changed.

        Modules present in DB but missing from disk are left alone here
        — :meth:`doctor` surfaces them as orphans.
        """
        discovered = self.discovered()
        existing = await self._load_existing_records()
        now = datetime.now(UTC)

        for module in discovered:
            try:
                manifest = module.get_manifest()
            except ManifestError as exc:
                logger.error(
                    "Skipping reconcile for %s (manifest invalid): %s",
                    module.name,
                    exc,
                )
                continue

            record = existing.get(module.name)
            if record is None:
                self.db.add(
                    ModuleRecord(
                        name=manifest.name,
                        version=manifest.version,
                        state=ModuleState.INSTALLED.value,
                        category=manifest.category.value,
                        removable=manifest.removable,
                        auto_install=manifest.auto_install,
                        installed_at=now,
                        last_state_change=now,
                        manifest_snapshot=manifest.to_snapshot(),
                    )
                )
                logger.info("Reconciled: inserted new module %s", manifest.name)
                continue

            if record.version != manifest.version:
                logger.info(
                    "Reconciled: %s version %s -> %s",
                    manifest.name,
                    record.version,
                    manifest.version,
                )
                record.version = manifest.version

            # Always refresh the snapshot so DB stays in sync with disk.
            record.manifest_snapshot = manifest.to_snapshot()
            record.category = manifest.category.value
            record.removable = manifest.removable
            record.auto_install = manifest.auto_install

        await self.db.commit()

    async def _load_existing_records(self) -> dict[str, ModuleRecord]:
        result = await self.db.execute(select(ModuleRecord))
        return {r.name: r for r in result.scalars()}

    # --- Query ----------------------------------------------------------

    async def list_modules(self) -> list[ModuleInfo]:
        """Return combined in-memory + DB view of all known modules."""
        records = await self._load_existing_records()
        discovered = {m.name: m for m in self.discovered()}

        names = sorted(set(records) | set(discovered))
        infos: list[ModuleInfo] = []

        for name in names:
            record = records.get(name)
            module = discovered.get(name)

            manifest = self._safe_manifest(module) if module else None
            summary = manifest.summary if manifest else ""
            depends = (
                list(manifest.depends)
                if manifest
                else list((record.manifest_snapshot or {}).get("depends", []))
            )
            version = manifest.version if manifest else (record.version if record else "")
            category = (
                manifest.category
                if manifest
                else ModuleCategory(record.category)
                if record
                else ModuleCategory.OFFICIAL
            )
            state = ModuleState(record.state) if record else ModuleState.UNINSTALLED

            infos.append(
                ModuleInfo(
                    name=name,
                    version=version,
                    state=state,
                    category=category,
                    removable=record.removable if record else True,
                    auto_install=record.auto_install if record else False,
                    installed_at=record.installed_at if record else None,
                    last_state_change=(record.last_state_change if record else datetime.now(UTC)),
                    base_revision=record.base_revision if record else None,
                    applied_revision=record.applied_revision if record else None,
                    error_message=record.error_message if record else None,
                    error_at=record.error_at if record else None,
                    summary=summary,
                    depends=depends,
                    in_disk=module is not None,
                )
            )

        return infos

    async def get_info(self, name: str) -> ModuleInfo | None:
        for info in await self.list_modules():
            if info.name == name:
                return info
        return None

    async def status(self) -> dict[str, Any]:
        """Summary: counts by state + list of pending + errored modules."""
        infos = await self.list_modules()
        by_state: dict[str, int] = {}
        pending: list[str] = []
        errored: list[str] = []

        for info in infos:
            by_state[info.state.value] = by_state.get(info.state.value, 0) + 1
            if info.state in {
                ModuleState.TO_INSTALL,
                ModuleState.TO_UPGRADE,
                ModuleState.TO_REMOVE,
            }:
                pending.append(info.name)
            if info.error_message:
                errored.append(info.name)

        return {
            "by_state": by_state,
            "pending": pending,
            "errored": errored,
            "total": len(infos),
        }

    async def doctor(self) -> DoctorReport:
        """Run diagnostic checks across discovered + persisted modules."""
        records = await self._load_existing_records()
        discovered = {m.name: m for m in self.discovered()}

        orphans: list[str] = [
            name
            for name, record in records.items()
            if name not in discovered
            and record.state not in (ModuleState.UNINSTALLED.value, ModuleState.DISABLED.value)
        ]

        manifest_errors: list[tuple[str, str]] = []
        for name, module in discovered.items():
            try:
                module.get_manifest()
            except ManifestError as exc:
                manifest_errors.append((name, str(exc)))

        known_names = set(discovered) | set(records)
        missing_deps: list[tuple[str, str]] = []
        for name, module in discovered.items():
            for dep in module.dependencies:
                if dep not in known_names:
                    missing_deps.append((name, dep))

        errored = [
            (name, record.error_message or "")
            for name, record in records.items()
            if record.error_message
        ]

        return DoctorReport(
            orphans=orphans,
            missing_dependencies=missing_deps,
            manifest_errors=manifest_errors,
            errored_modules=errored,
        )

    async def orphan(self, name: str) -> bool:
        """Mark a missing-from-disk module as ``uninstalled`` for recovery."""
        record = (
            await self.db.execute(select(ModuleRecord).where(ModuleRecord.name == name))
        ).scalar_one_or_none()
        if record is None:
            return False

        record.state = ModuleState.UNINSTALLED.value
        record.last_state_change = datetime.now(UTC)
        record.error_message = None
        record.error_at = None
        await self.db.commit()
        return True

    # --- Helpers --------------------------------------------------------

    @staticmethod
    def _safe_manifest(module: BaseModule) -> Manifest | None:
        try:
            return module.get_manifest()
        except ManifestError as exc:
            logger.error("Manifest error for %s: %s", module.name, exc)
            return None


async def rediscover_and_reconcile(db: AsyncSession) -> None:
    """Entry point used by the app lifespan.

    Assumes :func:`load_modules` already ran and filled the in-memory
    registry; this just mirrors the current state into ``core_module``.
    """
    svc = ModuleService(db)
    await svc.reconcile_with_db()
    # Also discover here in case `discover_modules()` was not called yet.
    if not module_registry.list_modules():
        discover_modules()
