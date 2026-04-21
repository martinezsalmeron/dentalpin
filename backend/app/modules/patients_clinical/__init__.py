"""patients_clinical — normalized medical history + emergency contacts.

Extracted from the JSONB blobs that lived on ``patients`` before Fase
B.4. Tables live under the ``patients_clinical_*`` prefix, one row per
allergy/medication/etc. (N:1 to patient) or per patient
(medical_context, emergency_contact, legal_guardian — all 1:1).

This module owns the ``patient.medical_updated`` event emission so the
timeline stays populated after the JSONB column is gone.
"""

from fastapi import APIRouter

from app.core.plugins import BaseModule

from .models import (
    Allergy,
    EmergencyContact,
    LegalGuardian,
    MedicalContext,
    Medication,
    SurgicalHistory,
    SystemicDisease,
)
from .router import router


class PatientsClinicalModule(BaseModule):
    """Normalized medical history + emergency contacts."""

    manifest = {
        "name": "patients_clinical",
        "version": "0.1.0",
        "summary": "Normalized medical history, allergies, medications, emergency contacts.",
        "author": "DentalPin Core Team",
        "license": "BSL-1.1",
        "category": "official",
        "depends": ["patients"],
        "installable": True,
        "auto_install": True,
        "removable": True,
        "role_permissions": {
            "admin": ["*"],
            "dentist": ["medical.read", "medical.write", "emergency.read", "emergency.write"],
            "hygienist": ["medical.read", "emergency.read"],
            "assistant": ["medical.read", "emergency.read", "emergency.write"],
            "receptionist": ["emergency.read", "emergency.write"],
        },
        "frontend": {
            "layer_path": "frontend",
        },
    }

    def get_models(self) -> list:
        return [
            MedicalContext,
            Allergy,
            Medication,
            SystemicDisease,
            SurgicalHistory,
            EmergencyContact,
            LegalGuardian,
        ]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return [
            "medical.read",
            "medical.write",
            "emergency.read",
            "emergency.write",
        ]

    def get_tools(self) -> list:
        return []
