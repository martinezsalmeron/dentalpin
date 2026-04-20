"""Clinical module database models.

Fase B transition: Patient lives in :mod:`app.modules.patients.models`
now. This module is being split; Appointment, AppointmentTreatment
and PatientTimeline remain here until B.2 / B.3.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin

# Re-export Patient so legacy imports such as
# ``from app.modules.clinical.models import Patient`` still resolve.
# This keeps the intermediate state working while we update callers
# module by module.
from app.modules.patients.models import Patient  # noqa: F401

if TYPE_CHECKING:
    from app.core.auth.models import Clinic, User
    from app.modules.catalog.models import TreatmentCatalogItem
    from app.modules.treatment_plan.models import PlannedTreatmentItem


class Appointment(Base, TimestampMixin):
    """Appointment entity."""

    __tablename__ = "appointments"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)
    patient_id: Mapped[UUID | None] = mapped_column(ForeignKey("patients.id"))
    professional_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    cabinet: Mapped[str] = mapped_column(String(50))
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    treatment_type: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="scheduled")
    # Status: scheduled, confirmed, in_progress, completed, cancelled, no_show
    notes: Mapped[str | None] = mapped_column(Text)
    color: Mapped[str | None] = mapped_column(String(7))  # Hex color

    # Relationships
    clinic: Mapped["Clinic"] = relationship(back_populates="appointments")
    patient: Mapped["Patient | None"] = relationship(back_populates="appointments")
    professional: Mapped["User"] = relationship()

    # Treatments (many-to-many via junction table)
    treatments: Mapped[list["AppointmentTreatment"]] = relationship(
        back_populates="appointment",
        cascade="all, delete-orphan",
        order_by="AppointmentTreatment.display_order",
    )

    # Partial unique index for conflict detection (excludes cancelled appointments)
    __table_args__ = (
        Index(
            "idx_appointment_slot",
            "clinic_id",
            "cabinet",
            "professional_id",
            "start_time",
            unique=True,
            postgresql_where=(status != "cancelled"),
        ),
    )


class AppointmentTreatment(Base):
    """Junction table linking appointments to planned treatment items.

    Primary link is to PlannedTreatmentItem. The catalog_item_id is derived
    from the planned item for convenience/denormalization.
    """

    __tablename__ = "appointment_treatments"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    appointment_id: Mapped[UUID] = mapped_column(
        ForeignKey("appointments.id", ondelete="CASCADE"), index=True
    )

    # Primary link: to treatment plan item
    planned_treatment_item_id: Mapped[UUID] = mapped_column(
        ForeignKey("planned_treatment_items.id"), index=True
    )

    # Denormalized catalog_item_id for query convenience (nullable for migration)
    catalog_item_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("treatment_catalog_items.id", ondelete="SET NULL"), nullable=True
    )

    display_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Completion tracking
    completed_in_appointment: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text, default=None)

    # Relationships
    appointment: Mapped["Appointment"] = relationship(back_populates="treatments")
    planned_item: Mapped["PlannedTreatmentItem"] = relationship()
    catalog_item: Mapped["TreatmentCatalogItem | None"] = relationship()


class PatientTimeline(Base):
    """Denormalized timeline of patient events for efficient retrieval."""

    __tablename__ = "patient_timeline"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)
    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id"), index=True)
    event_type: Mapped[str] = mapped_column(
        String(50)
    )  # appointment.completed, budget.created, etc.
    event_category: Mapped[str] = mapped_column(
        String(30)
    )  # visit, treatment, financial, communication, medical
    source_table: Mapped[str] = mapped_column(String(50))
    source_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    event_data: Mapped[dict | None] = mapped_column(JSONB)  # Additional structured data
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))

    # Relationships
    clinic: Mapped["Clinic"] = relationship()
    patient: Mapped["Patient"] = relationship(back_populates="timeline_entries")
    created_by_user: Mapped["User | None"] = relationship()

    __table_args__ = (
        Index("idx_timeline_patient_date", "patient_id", "occurred_at"),
        Index("idx_timeline_clinic_patient", "clinic_id", "patient_id"),
    )
