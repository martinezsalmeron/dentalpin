"""Periodontogram module — SEPA-standard periodontal charting and follow-up.

Optional, removable module. Lives as a sub-tab inside the **Diagnosis**
mode of ``ClinicalTab``, alongside the odontogram. Captures the nine SEPA
metrics per tooth across six probing sites and persists each session as
an immutable dated snapshot.

Coupling with ``odontogram`` is read-only: at draft creation the service
asks ``OdontogramService`` for tooth state to pre-fill
``is_present`` / ``is_implant`` flags. No FK is created — the module can
be uninstalled cleanly via its isolated Alembic branch.
"""

from fastapi import APIRouter

from app.core.plugins import BaseModule

from .events import on_odontogram_treatment_performed, on_patient_archived
from .models import PeriodontogramSite, PeriodontogramSnapshot, PeriodontogramTooth
from .router import router


class PeriodontogramModule(BaseModule):
    manifest = {
        "name": "periodontogram",
        "version": "0.1.0",
        "summary": ("SEPA periodontal charting — snapshots, probing sites, BoP/PI/CAL indices."),
        "author": "DentalPin Core Team",
        "license": "BSL-1.1",
        "category": "official",
        "depends": ["patients", "odontogram"],
        "installable": True,
        "auto_install": False,
        "removable": True,
        "role_permissions": {
            "admin": ["*"],
            "dentist": ["*"],
            "hygienist": ["read", "write"],
            "assistant": ["read"],
            "receptionist": [],
        },
        "frontend": {
            "layer_path": "frontend",
            "navigation": [],
        },
    }

    def get_models(self) -> list:
        return [PeriodontogramSnapshot, PeriodontogramTooth, PeriodontogramSite]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return ["read", "write"]

    def get_event_handlers(self) -> dict:
        return {
            "odontogram.treatment.performed": on_odontogram_treatment_performed,
            "patient.archived": on_patient_archived,
        }
