"""Agenda module — appointments + scheduling + cabinets."""

from fastapi import APIRouter

from app.core.plugins import BaseModule

from .models import Appointment, AppointmentTreatment
from .router import router


class AgendaModule(BaseModule):
    """Scheduling module: appointments, appointment treatments, cabinets."""

    manifest = {
        "name": "agenda",
        "version": "0.1.0",
        "summary": "Appointments, scheduling, cabinets.",
        "author": "DentalPin Core Team",
        "license": "BSL-1.1",
        "category": "official",
        "depends": ["patients", "catalog"],
        "installable": True,
        "auto_install": True,
        "removable": False,
        # Permissions remain under clinical.appointments.* during chunk
        # 1 so ROLE_PERMISSIONS + require_permission calls resolve
        # without churn. Chunk 2 renames them to agenda.appointments.*.
        "role_permissions": {
            "admin": ["*"],
        },
        "frontend": {
            "navigation": [
                {
                    "label": "nav.appointments",
                    "icon": "i-lucide-calendar",
                    "to": "/appointments",
                    "permission": "clinical.appointments.read",
                    "order": 20,
                },
            ],
        },
    }

    def get_models(self) -> list:
        return [Appointment, AppointmentTreatment]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        # Empty during chunk 1; chunk 2 declares agenda.appointments.*
        # and agenda.cabinets.* once ROLE_PERMISSIONS switches.
        return []
