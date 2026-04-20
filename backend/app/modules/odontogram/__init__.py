"""Odontogram module - dental charting and treatment tracking."""

import logging

from fastapi import APIRouter

from app.core.plugins import BaseModule

from .models import OdontogramHistory, ToothRecord, Treatment, TreatmentTooth
from .router import router

logger = logging.getLogger(__name__)


class OdontogramModule(BaseModule):
    """Odontogram module: tooth state + clinical treatments."""

    manifest = {
        "name": "odontogram",
        "version": "0.3.0",
        "summary": "Dental charting, tooth state, clinical treatments.",
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
            "hygienist": ["read", "write"],
            "assistant": ["read"],
            "receptionist": [],
        },
    }

    def get_models(self) -> list:
        return [ToothRecord, OdontogramHistory, Treatment, TreatmentTooth]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return [
            "read",
            "write",
            "treatments.read",
            "treatments.write",
        ]

    def get_event_handlers(self) -> dict:
        # Propagation from plan -> treatment performed now lives directly in
        # TreatmentPlanService.complete_item, so no subscriptions are needed here.
        return {}
