"""Patients module — patient identity.

Holds Patient, its schemas, service and the ``/api/v1/patients/*``
HTTP surface. Permissions re-namespace from ``clinical.patients.*``
to ``patients.*`` in chunk 3.
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
        # Permissions stay under the ``clinical.patients.*`` namespace
        # during B.1 chunk 2 to avoid churn on ROLE_PERMISSIONS.
        # Chunk 3 renames them to ``patients.*`` and updates every
        # caller + the frontend permissions config at once.
        "role_permissions": {
            "admin": ["*"],
        },
    }

    def get_models(self) -> list:
        return [Patient]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return []
