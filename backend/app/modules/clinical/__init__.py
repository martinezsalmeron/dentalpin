"""Clinical module - patients and appointments management."""
from fastapi import APIRouter

from app.core.plugins import BaseModule

from .models import Appointment, Patient
from .router import router


class ClinicalModule(BaseModule):
    """Clinical module providing patient and appointment management."""

    @property
    def name(self) -> str:
        return "clinical"

    @property
    def version(self) -> str:
        return "0.1.0"

    def get_models(self) -> list:
        return [Patient, Appointment]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return [
            "patients.read",
            "patients.write",
            "appointments.read",
            "appointments.write",
        ]
