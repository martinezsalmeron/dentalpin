"""Migration import module — DPMF importer.

Optional, installable/removable module that consumes a Dental Practice
Migration Format (DPMF v0.1) file produced by `dental-bridge` and
hydrates DentalPin's core modules with the extracted data.

Issue #78. The on-disk format is frozen and documented in
https://github.com/dentaltix/dental-bridge/blob/main/spec/dpmf-v0.1.md
— this module is the receiving end.

Key invariants:

- Cross-module FKs are confined to `media.documents` (binary staging).
  All other writes go through each target module's service layer so
  business events fire normally.
- `verifactu` is intentionally **not** declared in `manifest.depends`:
  Portuguese / French clinics must be able to import without it. The
  fiscal-document mapper detects verifactu at runtime via the module
  registry and gates legal-hash preservation behind operator opt-in.
- Idempotent: every persisted DentalPin row is recorded in
  ``entity_mappings`` keyed by ``(clinic_id, source_system,
  canonical_uuid, entity_type)`` so re-running a job is a no-op.
"""

from fastapi import APIRouter

from app.core.plugins import BaseModule

from .events import (
    on_appointment_created_for_progress,
)
from .lifecycle import install, uninstall
from .models import (
    EntityMapping,
    FileStaging,
    ImportJob,
    ImportWarning,
    RawEntity,
)
from .router import router


class MigrationImportModule(BaseModule):
    """Optional module that imports a DPMF file into the current clinic."""

    manifest = {
        "name": "migration_import",
        "version": "0.1.0",
        "summary": (
            "Importa datos de pacientes, citas, presupuestos, pagos y "
            "documentos desde un archivo DPMF generado por dental-bridge."
        ),
        "author": "DentalPin Core Team",
        "license": "BSL-1.1",
        "category": "official",
        # Hard module deps — every mapper below calls a service in one
        # of these. ``verifactu`` is intentionally OFF this list: the
        # fiscal-document mapper detects it at runtime so PT/FR clinics
        # without Spanish compliance can still import.
        "depends": [
            "patients",
            "schedules",
            "treatment_plan",
            "billing",
            "payments",
            "media",
        ],
        # Project convention: optional modules ship off; admin activates.
        "installable": True,
        "auto_install": False,
        "removable": True,
        "role_permissions": {
            # Migration is admin-only by default. A clinic operator
            # role can be widened from the manifest later if needed.
            "admin": ["*"],
        },
        "frontend": {
            "layer_path": "frontend",
            "navigation": [],  # surfaced via the settings registry, not the sidebar
        },
    }

    def get_models(self) -> list:
        return [ImportJob, EntityMapping, FileStaging, ImportWarning, RawEntity]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return [
            "job.read",
            "job.write",
            "job.execute",
            "binary.write",
        ]

    def get_event_handlers(self) -> dict:
        # Subscribe to our own progress signal so the BackgroundTask
        # pipeline can update ImportJob.processed_entities without
        # circular imports across the mappers.
        return {
            "migration.entity.persisted": on_appointment_created_for_progress,
        }

    async def install(self, ctx) -> None:  # noqa: D401 — lifecycle hook
        await install(ctx)

    async def uninstall(self, ctx) -> None:  # noqa: D401 — lifecycle hook
        await uninstall(ctx)
