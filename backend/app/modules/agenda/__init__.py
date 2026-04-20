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
        "role_permissions": {
            "admin": ["*"],
            "dentist": ["*"],
            "hygienist": ["appointments.read", "appointments.write"],
            "assistant": ["appointments.read", "appointments.write"],
            "receptionist": ["appointments.read", "appointments.write"],
        },
        "frontend": {
            "navigation": [
                {
                    "label": "nav.appointments",
                    "icon": "i-lucide-calendar",
                    "to": "/appointments",
                    "permission": "agenda.appointments.read",
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
        return [
            "appointments.read",
            "appointments.write",
            # Cabinets' CRUD still lives in agenda router but uses
            # admin.clinic.* during Fase B.2; chunk 3 introduces
            # agenda.cabinets.* alongside the cabinets table.
        ]
