"""Patient entity.

Fase B.4 dropped the JSONB medical blobs (``medical_history``,
``emergency_contact``, ``legal_guardian``) that used to live here;
those fields normalize into the ``patients_clinical`` module's
per-row tables. Alerts moved with them to
``PatientsClinicalService.compute_alerts``.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Boolean, Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.core.auth.models import Clinic
    from app.modules.agenda.models import Appointment
    from app.modules.patient_timeline.models import PatientTimeline


class Patient(Base, TimestampMixin):
    """Patient entity."""

    __tablename__ = "patients"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(255))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, archived
    # Operational opt-out: when true, recalls / outreach modules must
    # exclude the patient from active call lists and surface them in a
    # ``needs_review`` bucket instead.
    do_not_contact: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Extended demographics
    gender: Mapped[str | None] = mapped_column(String(20))  # male, female, other, prefer_not_say
    national_id: Mapped[str | None] = mapped_column(String(50))  # DNI/NIE/Passport
    national_id_type: Mapped[str | None] = mapped_column(String(20))  # dni, nie, passport
    profession: Mapped[str | None] = mapped_column(String(100))
    workplace: Mapped[str | None] = mapped_column(String(200))
    preferred_language: Mapped[str] = mapped_column(String(10), default="es")
    address: Mapped[dict | None] = mapped_column(JSONB)
    photo_url: Mapped[str | None] = mapped_column(String(500))

    # Billing
    billing_name: Mapped[str | None] = mapped_column(String(200), default=None)
    billing_tax_id: Mapped[str | None] = mapped_column(String(50), default=None)
    billing_address: Mapped[dict | None] = mapped_column(JSONB, default=None)
    billing_email: Mapped[str | None] = mapped_column(String(255), default=None)

    # Relationships
    clinic: Mapped[Clinic] = relationship(back_populates="patients")
    appointments: Mapped[list[Appointment]] = relationship(back_populates="patient")
    timeline_entries: Mapped[list[PatientTimeline]] = relationship(back_populates="patient")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def has_complete_billing_info(self) -> bool:
        """Check if patient has minimum billing info for invoicing."""
        return bool(self.billing_name and self.billing_tax_id)
