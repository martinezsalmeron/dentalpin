"""Patients module — patient identity.

Holds Patient, its schemas, service and the ``/api/v1/patients/*``
HTTP surface. Permissions use the ``patients.*`` namespace as of Fase
B.1 chunk 3.
"""

from fastapi import APIRouter

from app.core.plugins import BaseModule

from .models import Patient
from .router import router


class PatientsModule(BaseModule):
    """Identity module for Patient."""

    manifest = {
        "name": "patients",
        "version": "0.1.0",
        "summary": "Patient identity: name, contact, demographics, status.",
        "author": "DentalPin Core Team",
        "license": "BSL-1.1",
        "category": "official",
        "depends": [],
        "installable": True,
        "auto_install": True,
        "removable": False,
        "role_permissions": {
            "admin": ["*"],
            "dentist": ["*"],
            "hygienist": ["read"],
            "assistant": ["*"],
            "receptionist": ["read", "write"],
        },
        "frontend": {
            "layer_path": "frontend",
            "navigation": [
                {
                    "label": "nav.patients",
                    "icon": "i-lucide-users",
                    "to": "/patients",
                    "permission": "patients.read",
                    "order": 10,
                },
            ],
        },
    }

    def get_models(self) -> list:
        return [Patient]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return ["read", "write"]
