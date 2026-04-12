"""Clinical module database models."""

from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Date, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.core.auth.models import Clinic, User


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

    # Billing data
    billing_name: Mapped[str | None] = mapped_column(String(200), default=None)
    billing_tax_id: Mapped[str | None] = mapped_column(String(50), default=None)
    billing_address: Mapped[dict | None] = mapped_column(JSONB, default=None)
    billing_email: Mapped[str | None] = mapped_column(String(255), default=None)

    # Relationships
    clinic: Mapped["Clinic"] = relationship(back_populates="patients")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="patient")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def has_complete_billing_info(self) -> bool:
        """Check if patient has minimum billing info for invoicing."""
        return bool(self.billing_name and self.billing_tax_id)


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
