"""Odontogram module - dental charting and treatment tracking."""

import logging

from fastapi import APIRouter

from app.core.plugins import BaseModule

from .models import OdontogramHistory, ToothRecord, Treatment, TreatmentTooth
from .router import router

logger = logging.getLogger(__name__)


class OdontogramModule(BaseModule):
    """Odontogram module: tooth state + clinical treatments."""

    @property
    def name(self) -> str:
        return "odontogram"

    @property
    def version(self) -> str:
        return "0.3.0"

    @property
    def dependencies(self) -> list[str]:
        return ["clinical"]

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
