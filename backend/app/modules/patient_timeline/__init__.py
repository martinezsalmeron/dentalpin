"""patient_timeline — unified patient activity log.

Cross-module audit stream. Populated by event handlers that react to
patient.*, appointment.*, treatment.*, budget.*, invoice.*, email.*, and
document.* events from other modules.

Handlers live in ``events.py``. They read only from the event payload and
own their DB sessions, so the module stays removable in isolation (no
hard coupling to agenda / odontogram / budget / billing / etc.).
"""

from typing import Any

from fastapi import APIRouter

from app.core.events import EventType
from app.core.plugins import BaseModule

from . import events
from .models import PatientTimeline
from .router import router


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
        "frontend": {
            "layer_path": "frontend",
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
            # Visits
            EventType.APPOINTMENT_SCHEDULED: events.on_appointment_scheduled,
            EventType.APPOINTMENT_COMPLETED: events.on_appointment_completed,
            EventType.APPOINTMENT_CANCELLED: events.on_appointment_cancelled,
            EventType.APPOINTMENT_NO_SHOW: events.on_appointment_no_show,
            # Treatments
            EventType.ODONTOGRAM_TREATMENT_PERFORMED: events.on_tooth_treatment_performed,
            EventType.TREATMENT_PLAN_CREATED: events.on_plan_created,
            EventType.TREATMENT_PLAN_TREATMENT_COMPLETED: events.on_plan_item_completed,
            # Financial
            EventType.BUDGET_SENT: events.on_budget_sent,
            EventType.BUDGET_ACCEPTED: events.on_budget_accepted,
            EventType.INVOICE_ISSUED: events.on_invoice_issued,
            EventType.INVOICE_PAID: events.on_invoice_paid,
            # Communications
            EventType.EMAIL_SENT: events.on_email_sent,
            EventType.EMAIL_FAILED: events.on_email_failed,
            # Medical history
            EventType.PATIENT_MEDICAL_UPDATED: events.on_medical_updated,
            # Documents
            EventType.DOCUMENT_UPLOADED: events.on_document_uploaded,
        }
