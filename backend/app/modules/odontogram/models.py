"""Odontogram module database models."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.core.auth.models import Clinic, User
    from app.modules.clinical.models import Patient


class ToothRecord(Base, TimestampMixin):
    """Record of a single tooth's condition for a patient.

    Each record represents the current state of one tooth,
    including general condition and surface-specific conditions.
    """

    __tablename__ = "tooth_records"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)
    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id"), index=True)
    tooth_number: Mapped[int] = mapped_column(Integer)  # FDI notation: 11-48, 51-85
    tooth_type: Mapped[str] = mapped_column(String(20))  # permanent, deciduous
    general_condition: Mapped[str] = mapped_column(String(30), default="healthy")
    # Surface conditions: {"M": "healthy", "D": "caries", "O": "filling", "V": "healthy", "L": "healthy"}
    surfaces: Mapped[dict] = mapped_column(JSONB, default=dict)
    notes: Mapped[str | None] = mapped_column(Text)

    # Positional markers for orthodontic purposes
    is_displaced: Mapped[bool] = mapped_column(Boolean, default=False)
    is_rotated: Mapped[bool] = mapped_column(Boolean, default=False)
    displacement_notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    clinic: Mapped["Clinic"] = relationship()
    patient: Mapped["Patient"] = relationship()
    treatments: Mapped[list["ToothTreatment"]] = relationship(
        back_populates="tooth_record", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("patient_id", "tooth_number", name="uq_patient_tooth"),
        Index("idx_tooth_records_patient", "patient_id"),
        Index("idx_tooth_records_clinic_patient", "clinic_id", "patient_id"),
    )


class ToothTreatment(Base, TimestampMixin):
    """Individual treatment record for a tooth.

    Stores treatments with their status (existing/planned)
    for tracking treatment history and integration with budgets.
    """

    __tablename__ = "tooth_treatments"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)
    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id"), index=True)
    tooth_record_id: Mapped[UUID] = mapped_column(ForeignKey("tooth_records.id"), index=True)
    tooth_number: Mapped[int] = mapped_column(Integer)  # Denormalized for queries

    # Treatment identification
    treatment_type: Mapped[str] = mapped_column(String(30))  # filling, crown, implant, etc.
    treatment_category: Mapped[str] = mapped_column(String(20))  # surface, whole_tooth

    # Surface treatments only
    surfaces: Mapped[list | None] = mapped_column(JSONB)  # ["M", "O"] for MO filling

    # Status (key concept for Gesdén style)
    status: Mapped[str] = mapped_column(String(20), default="existing")  # existing, planned

    # Audit timestamps
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    performed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    performed_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))

    # Integration with budget module
    budget_item_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True)
    )  # FK to budget item if applicable
    source_module: Mapped[str] = mapped_column(
        String(30), default="odontogram"
    )  # Which module created this

    notes: Mapped[str | None] = mapped_column(Text)

    # Soft delete support
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    # Relationships
    clinic: Mapped["Clinic"] = relationship()
    patient: Mapped["Patient"] = relationship()
    tooth_record: Mapped["ToothRecord"] = relationship(back_populates="treatments")
    performer: Mapped["User | None"] = relationship(foreign_keys=[performed_by])

    __table_args__ = (
        Index("idx_tooth_treatments_patient", "patient_id"),
        Index("idx_tooth_treatments_tooth_record", "tooth_record_id"),
        Index("idx_tooth_treatments_status", "patient_id", "status"),
        Index("idx_tooth_treatments_budget", "budget_item_id"),
    )


class OdontogramHistory(Base):
    """Audit log for odontogram changes.

    Records every change made to a tooth's condition for traceability.
    """

    __tablename__ = "odontogram_history"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)
    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id"), index=True)
    tooth_number: Mapped[int] = mapped_column(Integer)
    change_type: Mapped[str] = mapped_column(String(30))  # surface_update, general_condition, note
    surface: Mapped[str | None] = mapped_column(String(1))  # M, D, O, V, L (null for general)
    old_condition: Mapped[str | None] = mapped_column(String(30))
    new_condition: Mapped[str | None] = mapped_column(String(30))
    notes: Mapped[str | None] = mapped_column(Text)
    changed_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Relationships
    clinic: Mapped["Clinic"] = relationship()
    patient: Mapped["Patient"] = relationship()
    user: Mapped["User"] = relationship()

    __table_args__ = (
        Index("idx_odontogram_history_patient", "patient_id"),
        Index("idx_odontogram_history_tooth", "patient_id", "tooth_number"),
    )
