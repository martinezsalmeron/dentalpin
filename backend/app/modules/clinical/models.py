"""Clinical module database models."""

from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.core.auth.models import Clinic, User
    from app.modules.catalog.models import TreatmentCatalogItem
    from app.modules.treatment_plan.models import PlannedTreatmentItem


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

    # Extended demographics
    gender: Mapped[str | None] = mapped_column(String(20))  # male, female, other, prefer_not_say
    national_id: Mapped[str | None] = mapped_column(String(50))  # DNI/NIE/Passport
    national_id_type: Mapped[str | None] = mapped_column(String(20))  # dni, nie, passport
    profession: Mapped[str | None] = mapped_column(String(100))
    workplace: Mapped[str | None] = mapped_column(String(200))
    preferred_language: Mapped[str] = mapped_column(String(10), default="es")
    address: Mapped[dict | None] = mapped_column(
        JSONB
    )  # street, city, postal_code, province, country
    photo_url: Mapped[str | None] = mapped_column(String(500))

    # Emergency contact (JSONB)
    emergency_contact: Mapped[dict | None] = mapped_column(JSONB)
    # {name, relationship, phone, email, is_legal_guardian}

    # Legal guardian for minors (JSONB)
    legal_guardian: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # {name, relationship, dni, phone, email, address, notes}

    # Medical history (JSONB)
    medical_history: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    # Billing data
    billing_name: Mapped[str | None] = mapped_column(String(200), default=None)
    billing_tax_id: Mapped[str | None] = mapped_column(String(50), default=None)
    billing_address: Mapped[dict | None] = mapped_column(JSONB, default=None)
    billing_email: Mapped[str | None] = mapped_column(String(255), default=None)

    # Relationships
    clinic: Mapped["Clinic"] = relationship(back_populates="patients")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="patient")
    timeline_entries: Mapped[list["PatientTimeline"]] = relationship(back_populates="patient")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def has_complete_billing_info(self) -> bool:
        """Check if patient has minimum billing info for invoicing."""
        return bool(self.billing_name and self.billing_tax_id)

    @property
    def active_alerts(self) -> list[dict]:
        """Compute active alerts from medical_history."""
        alerts = []
        mh = self.medical_history or {}

        # Allergies (severity high or critical)
        for allergy in mh.get("allergies", []):
            if allergy.get("severity") in ("high", "critical"):
                alerts.append(
                    {
                        "type": "allergy",
                        "severity": allergy.get("severity", "high"),
                        "title": f"Alergia: {allergy.get('name', 'Desconocida')}",
                        "details": allergy.get("reaction"),
                    }
                )

        # Pregnancy
        if mh.get("is_pregnant"):
            week = mh.get("pregnancy_week")
            alerts.append(
                {
                    "type": "pregnancy",
                    "severity": "high",
                    "title": f"Embarazada{f' ({week} semanas)' if week else ''}",
                    "details": None,
                }
            )

        # Lactating
        if mh.get("is_lactating"):
            alerts.append(
                {
                    "type": "lactating",
                    "severity": "medium",
                    "title": "En período de lactancia",
                    "details": None,
                }
            )

        # Anticoagulants
        if mh.get("is_on_anticoagulants"):
            med = mh.get("anticoagulant_medication")
            inr = mh.get("inr_value")
            alerts.append(
                {
                    "type": "anticoagulant",
                    "severity": "critical",
                    "title": f"Anticoagulantes{f': {med}' if med else ''}",
                    "details": f"INR: {inr}" if inr else None,
                }
            )

        # Anesthesia adverse reactions
        if mh.get("adverse_reactions_to_anesthesia"):
            alerts.append(
                {
                    "type": "anesthesia_reaction",
                    "severity": "critical",
                    "title": "Reacción adversa a anestesia",
                    "details": mh.get("anesthesia_reaction_details"),
                }
            )

        # Critical systemic diseases
        for disease in mh.get("systemic_diseases", []):
            if disease.get("is_critical"):
                alerts.append(
                    {
                        "type": "systemic_disease",
                        "severity": "high",
                        "title": disease.get("name", "Enfermedad sistémica"),
                        "details": disease.get("notes"),
                    }
                )

        return alerts


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
