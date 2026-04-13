"""Clinical module - patients and appointments management."""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import EventType
from app.core.plugins import BaseModule

from .models import Appointment, AppointmentTreatment, Patient, PatientTimeline
from .router import router
from .service import TimelineService


class ClinicalModule(BaseModule):
    """Clinical module providing patient and appointment management."""

    @property
    def name(self) -> str:
        return "clinical"

    @property
    def version(self) -> str:
        return "0.1.0"

    def get_models(self) -> list:
        return [Patient, Appointment, AppointmentTreatment, PatientTimeline]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return [
            "patients.read",
            "patients.write",
            "patients.medical.read",
            "patients.medical.write",
            "appointments.read",
            "appointments.write",
        ]

    def get_event_handlers(self) -> dict[str, Any]:
        """Register event handlers for timeline population."""
        return {
            EventType.APPOINTMENT_COMPLETED: self._on_appointment_completed,
            EventType.APPOINTMENT_CANCELLED: self._on_appointment_cancelled,
            EventType.PATIENT_MEDICAL_UPDATED: self._on_medical_updated,
        }

    async def _on_appointment_completed(self, db: AsyncSession, data: dict) -> None:
        """Add timeline entry when appointment is completed."""
        appointment_id = UUID(data["appointment_id"])
        # We need clinic_id to query - fetch from appointment
        from sqlalchemy import select

        result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
        appointment = result.scalar_one_or_none()
        if not appointment or not appointment.patient_id:
            return

        await TimelineService.add_entry(
            db=db,
            clinic_id=appointment.clinic_id,
            patient_id=appointment.patient_id,
            event_type=EventType.APPOINTMENT_COMPLETED,
            event_category="visit",
            source_table="appointments",
            source_id=appointment_id,
            title=f"Cita completada: {appointment.treatment_type or 'Consulta'}",
            description=appointment.notes,
            event_data={
                "cabinet": appointment.cabinet,
                "professional_id": str(appointment.professional_id),
            },
            occurred_at=appointment.end_time or datetime.utcnow(),
        )

    async def _on_appointment_cancelled(self, db: AsyncSession, data: dict) -> None:
        """Add timeline entry when appointment is cancelled."""
        appointment_id = UUID(data["appointment_id"])
        from sqlalchemy import select

        result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
        appointment = result.scalar_one_or_none()
        if not appointment or not appointment.patient_id:
            return

        await TimelineService.add_entry(
            db=db,
            clinic_id=appointment.clinic_id,
            patient_id=appointment.patient_id,
            event_type=EventType.APPOINTMENT_CANCELLED,
            event_category="visit",
            source_table="appointments",
            source_id=appointment_id,
            title=f"Cita cancelada: {appointment.treatment_type or 'Consulta'}",
            occurred_at=datetime.utcnow(),
        )

    async def _on_medical_updated(self, db: AsyncSession, data: dict) -> None:
        """Add timeline entry when medical history is updated."""
        patient_id = UUID(data["patient_id"])
        clinic_id = UUID(data["clinic_id"])
        user_id = UUID(data["user_id"]) if data.get("user_id") else None

        await TimelineService.add_entry(
            db=db,
            clinic_id=clinic_id,
            patient_id=patient_id,
            event_type=EventType.PATIENT_MEDICAL_UPDATED,
            event_category="medical",
            source_table="patients",
            source_id=patient_id,
            title="Historia clínica actualizada",
            occurred_at=datetime.utcnow(),
            created_by=user_id,
        )
