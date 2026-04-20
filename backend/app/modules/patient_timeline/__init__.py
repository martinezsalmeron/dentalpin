"""patient_timeline — unified patient activity log.

Cross-module audit stream. Populated by event handlers that react to
patient.*, appointment.*, document.* events from other modules.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import EventType
from app.core.plugins import BaseModule

from .models import PatientTimeline
from .router import router
from .service import TimelineService


class PatientTimelineModule(BaseModule):
    """Timeline module: logs cross-module patient events."""

    manifest = {
        "name": "patient_timeline",
        "version": "0.1.0",
        "summary": "Patient timeline — unified activity log.",
        "author": "DentalPin Core Team",
        "license": "BSL-1.1",
        "category": "official",
        "depends": ["patients"],
        "installable": True,
        "auto_install": True,
        "removable": True,
        "role_permissions": {
            "admin": ["*"],
            "dentist": ["read"],
            "hygienist": ["read"],
            "assistant": ["read"],
            "receptionist": ["read"],
        },
    }

    def get_models(self) -> list:
        return [PatientTimeline]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return ["read"]

    def get_event_handlers(self) -> dict[str, Any]:
        """Populate the timeline from other modules' events."""
        return {
            EventType.APPOINTMENT_COMPLETED: self._on_appointment_completed,
            EventType.APPOINTMENT_CANCELLED: self._on_appointment_cancelled,
            EventType.PATIENT_MEDICAL_UPDATED: self._on_medical_updated,
            EventType.DOCUMENT_UPLOADED: self._on_document_uploaded,
        }

    async def _on_appointment_completed(self, db: AsyncSession, data: dict) -> None:
        """Log an appointment completion."""
        from sqlalchemy import select

        from app.modules.agenda.models import Appointment

        appointment_id = UUID(data["appointment_id"])
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
        """Log an appointment cancellation."""
        from sqlalchemy import select

        from app.modules.agenda.models import Appointment

        appointment_id = UUID(data["appointment_id"])
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
        """Log a medical history update."""
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

    async def _on_document_uploaded(self, db: AsyncSession, data: dict) -> None:
        """Log a document upload."""
        document_id = UUID(data["document_id"])
        patient_id = UUID(data["patient_id"])
        clinic_id = UUID(data["clinic_id"])

        await TimelineService.add_entry(
            db=db,
            clinic_id=clinic_id,
            patient_id=patient_id,
            event_type=EventType.DOCUMENT_UPLOADED,
            event_category="document",
            source_table="documents",
            source_id=document_id,
            title=f"Documento: {data['title']}",
            event_data={"document_type": data["document_type"]},
            occurred_at=datetime.utcnow(),
        )
