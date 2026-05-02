"""Media module database models."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
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
    from app.core.auth.models import Clinic, User
    from app.modules.patients.models import Patient


class Document(Base, TimestampMixin):
    """Document entity for patient files.

    Covers PDFs, clinical photos, X-rays and any other patient asset.
    The ``media_kind`` column drives UI behaviour (gallery vs document
    list) while ``document_type`` keeps its administrative meaning
    (consent, insurance, etc.) for the document-list use case.
    """

    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)
    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id"), index=True)

    # Administrative classification (consent / insurance / report / ...).
    document_type: Mapped[str] = mapped_column(String(30))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)

    # File metadata
    original_filename: Mapped[str] = mapped_column(String(255))
    storage_path: Mapped[str] = mapped_column(String(500), unique=True)
    mime_type: Mapped[str] = mapped_column(String(100))
    file_size: Mapped[int] = mapped_column(Integer)

    # Media taxonomy. ``media_kind`` is the UI rail; ``media_category``
    # and ``media_subtype`` only carry meaning for kind ∈ {photo, xray}.
    # Validation is enforced service-side via ``photo_taxonomy``.
    media_kind: Mapped[str] = mapped_column(
        String(20), default="document", server_default="document"
    )
    media_category: Mapped[str | None] = mapped_column(String(20))
    media_subtype: Mapped[str | None] = mapped_column(String(40))

    # Capture timestamp from EXIF (or manual override). Falls back to
    # ``created_at`` when null in queries.
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Before/after pairing. Self-referential, same patient guaranteed
    # by service layer + CHECK below (self != id).
    paired_document_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="SET NULL"),
    )

    # Free-form labels (["composite", "tooth-26"]) for power search.
    tags: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )

    # Extensibility hatch (storage backend hints, thumbnail status, etc.).
    extra_data: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    # Audit
    uploaded_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, archived

    # Relationships
    clinic: Mapped["Clinic"] = relationship()
    patient: Mapped["Patient"] = relationship()
    uploader: Mapped["User"] = relationship()
    paired_document: Mapped["Document | None"] = relationship(
        "Document",
        remote_side="Document.id",
        foreign_keys=[paired_document_id],
        post_update=True,
    )

    __table_args__ = (
        Index("idx_documents_clinic_patient", "clinic_id", "patient_id"),
        Index("idx_documents_type", "clinic_id", "document_type"),
        Index(
            "idx_documents_clinic_patient_kind_captured",
            "clinic_id",
            "patient_id",
            "media_kind",
            "captured_at",
        ),
        CheckConstraint(
            "paired_document_id IS NULL OR paired_document_id <> id",
            name="ck_documents_pair_not_self",
        ),
    )


class MediaAttachment(Base, TimestampMixin):
    """Polymorphic link between a ``Document`` and an arbitrary owner.

    The owning module declares its ``owner_type`` strings in
    ``media.attachment_registry`` and provides a resolver that maps
    ``owner_id -> patient_id``. The registry validates the link at
    service time; we deliberately do **not** add a CHECK constraint on
    ``owner_type`` because the taxonomy is dynamic (depends on which
    modules are installed).

    There is also no FK on ``owner_id`` — that would require polymorphic
    FK trickery and break uninstall safety. Trust the service layer.
    """

    __tablename__ = "media_attachments"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    owner_type: Mapped[str] = mapped_column(String(40))
    owner_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True))
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    document: Mapped["Document"] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "owner_type",
            "owner_id",
            name="uq_media_attachments_doc_owner",
        ),
        Index(
            "idx_media_attachments_owner",
            "clinic_id",
            "owner_type",
            "owner_id",
        ),
    )
