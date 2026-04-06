"""Odontogram module - dental charting and tooth condition tracking."""

from fastapi import APIRouter

from app.core.plugins import BaseModule

from .models import OdontogramHistory, ToothRecord, ToothTreatment
from .router import router


class OdontogramModule(BaseModule):
    """Odontogram module providing dental charting functionality."""

    @property
    def name(self) -> str:
        return "odontogram"

    @property
    def version(self) -> str:
        return "0.2.0"

    @property
    def dependencies(self) -> list[str]:
        return ["clinical"]  # Depends on clinical for Patient model

    def get_models(self) -> list:
        return [ToothRecord, OdontogramHistory, ToothTreatment]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return [
            "read",
            "write",
            "treatments.read",
            "treatments.write",
        ]
