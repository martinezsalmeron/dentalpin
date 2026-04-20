"""Patient entity.

Moved from ``app.modules.clinical.models`` as part of Fase B. The
backing table is still ``patients`` (same name, same columns), so
cross-module FKs like ``budgets.patient_id → patients.id`` continue
to resolve without any schema change.

JSONB fields (``medical_history``, ``emergency_contact``,
``legal_guardian``) stay on this row for now; they normalize into
separate ``patients_clinical`` tables in Etapa B.4.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.core.auth.models import Clinic
    from app.modules.agenda.models import Appointment
    from app.modules.clinical.models import PatientTimeline


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
    address: Mapped[dict | None] = mapped_column(JSONB)
    photo_url: Mapped[str | None] = mapped_column(String(500))

    # JSONB fields (to be normalized into patients_clinical module in B.4).
    emergency_contact: Mapped[dict | None] = mapped_column(JSONB)
    legal_guardian: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    medical_history: Mapped[dict | None] = mapped_column(JSONB, default=dict)

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

    @property
    def active_alerts(self) -> list[dict]:
        """Compute active alerts from medical_history.

        Stays on Patient during B.1; migrates to patients_clinical with
        the JSONB normalization in B.4.
        """
        alerts: list[dict] = []
        mh = self.medical_history or {}

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

        if mh.get("is_lactating"):
            alerts.append(
                {
                    "type": "lactating",
                    "severity": "medium",
                    "title": "En período de lactancia",
                    "details": None,
                }
            )

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

        if mh.get("adverse_reactions_to_anesthesia"):
            alerts.append(
                {
                    "type": "anesthesia_reaction",
                    "severity": "critical",
                    "title": "Reacción adversa a anestesia",
                    "details": mh.get("anesthesia_reaction_details"),
                }
            )

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
