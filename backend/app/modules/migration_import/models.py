"""SQLAlchemy models for the DPMF importer.

All five tables live on the dedicated ``migration_import`` Alembic
branch and are cascade-dropped on uninstall. The only outbound FK to
another module's table is :attr:`FileStaging.resolved_document_id`
(``media.documents``); everything else points to core tables
(``clinics``, ``users``) or to ImportJob itself.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin

if TYPE_CHECKING:
    pass


class ImportJob(Base, TimestampMixin):
    """One row per uploaded DPMF file.

    State machine: ``uploaded`` → ``validating`` → ``validated`` →
    ``previewing`` → ``executing`` → ``completed`` / ``failed``.

    ``last_checkpoint`` is the breadcrumb used to resume mid-execution
    after a process restart. The actual idempotency guarantee lives in
    :class:`EntityMapping`, so a resume that re-runs already-applied
    rows is safe — it just wastes work.
    """

    __tablename__ = "migration_import_jobs"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), index=True, nullable=False
    )
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="uploaded")
    # State transitions write here so the UI surfaces actionable errors.
    error: Mapped[str | None] = mapped_column(Text)

    # File staging on disk — kept out of `media` storage because these
    # are raw DPMF blobs, not patient assets. Removed on job deletion.
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    # _meta fields, populated during validate.
    source_system: Mapped[str | None] = mapped_column(String(50))
    source_adapter_version: Mapped[str | None] = mapped_column(String(30))
    exporter_tool: Mapped[str | None] = mapped_column(String(50))
    exporter_version: Mapped[str | None] = mapped_column(String(30))
    format_version: Mapped[str | None] = mapped_column(String(20))
    tenant_label: Mapped[str | None] = mapped_column(String(255))
    integrity_hash_declared: Mapped[str | None] = mapped_column(String(128))
    integrity_hash_computed: Mapped[str | None] = mapped_column(String(128))

    # Progress.
    total_entities: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processed_entities: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_checkpoint: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    # Operator opt-ins captured at execute time.
    import_fiscal_compliance: Mapped[bool] = mapped_column(
        default=False, server_default="false", nullable=False
    )

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships — orphan-cascade so admin-side `DELETE /jobs/{id}`
    # cleans staging + mappings + warnings in one shot.
    mappings: Mapped[list[EntityMapping]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    file_stagings: Mapped[list[FileStaging]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    warnings: Mapped[list[ImportWarning]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    raw_entities: Mapped[list[RawEntity]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )


class EntityMapping(Base, TimestampMixin):
    """`(source_system, canonical_uuid, entity_type)` → DentalPin row.

    The idempotency keystone. Every mapper consults this first; if the
    triple is already present for the job's clinic, the mapper returns
    without writing.

    The UNIQUE constraint includes ``clinic_id`` so two clinics can
    independently import the same DPMF without colliding on UUIDs.
    """

    __tablename__ = "migration_import_entity_mappings"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), index=True, nullable=False
    )
    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("migration_import_jobs.id", ondelete="CASCADE"), index=True, nullable=False
    )

    source_system: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_canonical_uuid: Mapped[str] = mapped_column(String(36), nullable=False)

    dentalpin_table: Mapped[str] = mapped_column(String(60), nullable=False)
    dentalpin_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)

    job: Mapped[ImportJob] = relationship(back_populates="mappings")

    __table_args__ = (
        UniqueConstraint(
            "clinic_id",
            "source_system",
            "entity_type",
            "source_canonical_uuid",
            name="uq_migration_entity_mapping_lookup",
        ),
        Index(
            "ix_migration_entity_mapping_clinic_entity",
            "clinic_id",
            "entity_type",
        ),
    )


class FileStaging(Base, TimestampMixin):
    """One row per `_files` manifest entry.

    Created during execute when the document mapper runs. The sync
    agent later POSTs each binary against ``/jobs/{id}/binaries``;
    the receiver looks up the row by ``(job_id, sha256)``, deposits
    the bytes through ``media.DocumentService``, and flips status.
    """

    __tablename__ = "migration_import_file_stagings"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), index=True, nullable=False
    )
    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("migration_import_jobs.id", ondelete="CASCADE"), index=True, nullable=False
    )

    canonical_uuid: Mapped[str] = mapped_column(String(36), nullable=False)
    parent_entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    parent_canonical_uuid: Mapped[str] = mapped_column(String(36), nullable=False)

    relative_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    declared_size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    # sha256 may be null when the extractor couldn't read the file; the
    # operator sees a warning and the binary cannot be matched.
    sha256: Mapped[str | None] = mapped_column(String(64))
    mime_hint: Mapped[str | None] = mapped_column(String(100))

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_document_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="SET NULL"),
    )

    job: Mapped[ImportJob] = relationship(back_populates="file_stagings")

    __table_args__ = (
        UniqueConstraint("job_id", "canonical_uuid", name="uq_migration_file_staging_canonical"),
        Index("ix_migration_file_staging_lookup", "job_id", "sha256"),
    )


class ImportWarning(Base, TimestampMixin):
    """Audit row mirroring DPMF's `_warnings` + warnings the importer raises."""

    __tablename__ = "migration_import_warnings"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("migration_import_jobs.id", ondelete="CASCADE"), index=True, nullable=False
    )

    entity_type: Mapped[str | None] = mapped_column(String(50))
    source_id: Mapped[str | None] = mapped_column(String(100))
    severity: Mapped[str] = mapped_column(String(10), nullable=False, default="info")
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    raw_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    job: Mapped[ImportJob] = relationship(back_populates="warnings")


class RawEntity(Base, TimestampMixin):
    """Catch-all for DPMF entities without a dedicated mapper today.

    Forward-compat hatch: the day a target module appears in DentalPin
    we can rehydrate from these rows instead of asking the operator to
    re-import the file.
    """

    __tablename__ = "migration_import_raw_entities"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), index=True, nullable=False
    )
    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("migration_import_jobs.id", ondelete="CASCADE"), index=True, nullable=False
    )

    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    canonical_uuid: Mapped[str] = mapped_column(String(36), nullable=False)
    source_system: Mapped[str] = mapped_column(String(50), nullable=False)
    source_id: Mapped[str] = mapped_column(String(100), nullable=False)

    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    raw_source_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    job: Mapped[ImportJob] = relationship(back_populates="raw_entities")

    __table_args__ = (
        UniqueConstraint("job_id", "entity_type", "canonical_uuid", name="uq_migration_raw_entity"),
        Index("ix_migration_raw_entity_clinic_type", "clinic_id", "entity_type"),
    )
