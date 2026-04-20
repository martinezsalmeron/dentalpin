"""Agenda models — appointments + linked treatments.

Moved from ``app.modules.clinical.models`` in Fase B.2 chunk 1. The
backing tables (``appointments``, ``appointment_treatments``) keep
their name and schema, so cross-module FKs resolve unchanged.

Cabinets still live as a JSONB column on ``clinic.cabinets`` during
chunk 1; chunk 3 extracts them into their own table with
``appointment.cabinet_id`` as FK.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.core.auth.models import Clinic, User
    from app.modules.catalog.models import TreatmentCatalogItem
    from app.modules.patients.models import Patient
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
    notes: Mapped[str | None] = mapped_column(Text)
    color: Mapped[str | None] = mapped_column(String(7))

    clinic: Mapped[Clinic] = relationship(back_populates="appointments")
    patient: Mapped[Patient | None] = relationship(back_populates="appointments")
    professional: Mapped[User] = relationship()

    treatments: Mapped[list[AppointmentTreatment]] = relationship(
        back_populates="appointment",
        cascade="all, delete-orphan",
        order_by="AppointmentTreatment.display_order",
    )

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
    """Junction table linking appointments to planned treatment items."""

    __tablename__ = "appointment_treatments"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    appointment_id: Mapped[UUID] = mapped_column(
        ForeignKey("appointments.id", ondelete="CASCADE"), index=True
    )
    planned_treatment_item_id: Mapped[UUID] = mapped_column(
        ForeignKey("planned_treatment_items.id"), index=True
    )
    catalog_item_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("treatment_catalog_items.id", ondelete="SET NULL"), nullable=True
    )
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_in_appointment: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text, default=None)

    appointment: Mapped[Appointment] = relationship(back_populates="treatments")
    planned_item: Mapped[PlannedTreatmentItem] = relationship()
    catalog_item: Mapped[TreatmentCatalogItem | None] = relationship()
