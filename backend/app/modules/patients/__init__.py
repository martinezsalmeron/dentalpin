"""Patients module — patient identity.

Fase B foundation: Patient model lives here. Schemas, router and
service are being migrated from `clinical` in subsequent chunks of
B.1. Until the migration completes, the Patient CRUD endpoints remain
mounted at ``/api/v1/clinical/patients/*`` via the clinical router.
"""

from fastapi import APIRouter

from app.core.plugins import BaseModule

from .models import Patient


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
        # Permissions + role mapping arrive in chunk 3 of B.1 alongside
        # the router move. During chunk 1 the HTTP surface still lives
        # in the clinical router, so patients declares no runtime
        # permissions yet.
        "role_permissions": {
            "admin": ["*"],
        },
    }

    def get_models(self) -> list:
        return [Patient]

    def get_router(self) -> APIRouter:
        # Router is empty during B.1 chunk 1 — endpoints still live in
        # the clinical router. They will move here in chunk 2.
        return APIRouter()

    def get_permissions(self) -> list[str]:
        return []
