"""Pydantic schemas for the migration_import HTTP surface."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ImportJobResponse(BaseModel):
    """Public view of an :class:`ImportJob`."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID
    created_by: UUID
    status: str
    error: str | None

    original_filename: str
    file_size: int

    source_system: str | None
    exporter_tool: str | None
    exporter_version: str | None
    format_version: str | None
    tenant_label: str | None
    integrity_hash_declared: str | None
    integrity_hash_computed: str | None

    total_entities: int
    processed_entities: int

    import_fiscal_compliance: bool

    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ValidateRequest(BaseModel):
    """Optional passphrase for encrypted DPMFs.

    Sent on POST /jobs/{id}/validate so the passphrase never lives in
    the ImportJob row. Held only in process memory during the call.
    """

    passphrase: str | None = None


class PreviewSample(BaseModel):
    """One sample row in the preview response."""

    canonical_uuid: str
    source_id: str
    payload: dict[str, Any]


class EntityPreview(BaseModel):
    entity_type: str
    declared_count: int
    samples: list[PreviewSample] = Field(default_factory=list)


class WarningView(BaseModel):
    severity: str
    code: str
    message: str
    entity_type: str | None = None
    source_id: str | None = None


class FilesManifestSummary(BaseModel):
    total: int
    with_sha256: int
    without_sha256: int


class PreviewResponse(BaseModel):
    job: ImportJobResponse
    entities: list[EntityPreview]
    warnings: list[WarningView]
    files: FilesManifestSummary
    # Verifactu opt-in surface — UI hides the checkbox unless both are true.
    verifactu_data_detected: bool
    verifactu_module_installed: bool


class ExecuteRequest(BaseModel):
    """Operator opt-ins for the execute phase."""

    import_fiscal_compliance: bool = False
    # Passphrase repeated only if the file is encrypted; preview already
    # accepted it but execute runs in a fresh BackgroundTask process,
    # so we need it again to re-open the file.
    passphrase: str | None = None


class WarningResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: UUID
    entity_type: str | None
    source_id: str | None
    severity: str
    code: str
    message: str
    raw_data: dict[str, Any] | None
    created_at: datetime
