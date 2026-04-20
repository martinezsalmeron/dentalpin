"""Media module database models."""

from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.core.auth.models import Clinic, User
    from app.modules.patients.models import Patient


class Document(Base, TimestampMixin):
    """Document entity for patient files."""

    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)
    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id"), index=True)

    # Document metadata
    document_type: Mapped[str] = mapped_column(
        String(30)
    )  # consent, id_scan, insurance, report, referral, other
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)

    # File metadata
    original_filename: Mapped[str] = mapped_column(String(255))
    storage_path: Mapped[str] = mapped_column(String(500), unique=True)
    mime_type: Mapped[str] = mapped_column(String(100))
    file_size: Mapped[int] = mapped_column(Integer)

    # Extensibility
    extra_data: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    # Audit
    uploaded_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, archived

    # Relationships
    clinic: Mapped["Clinic"] = relationship()
    patient: Mapped["Patient"] = relationship()
    uploader: Mapped["User"] = relationship()

    __table_args__ = (
        Index("idx_documents_clinic_patient", "clinic_id", "patient_id"),
        Index("idx_documents_type", "clinic_id", "document_type"),
    )
