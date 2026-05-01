"""Recalls module — patient call-back workflow.

Issue #62. Optional, removable. Sibling to agenda + patients.

The module owns the recall state machine + monthly call list +
``recall_settings``. It consumes events from agenda, patients and
treatment_plan; it never imports any of those modules' models or
services. Treatment-plan integration goes through the enriched
``treatment_plan.treatment_completed`` payload (``treatment_category_key``
snapshot) so we keep the dependency at ``["patients", "agenda"]``.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.plugins import BaseModule

from .events import (
    on_appointment_cancelled,
    on_appointment_completed,
    on_appointment_scheduled,
    on_patient_archived,
    on_treatment_plan_completed,
)
from .models import Recall, RecallContactAttempt, RecallSettings
from .router import router


class RecallsModule(BaseModule):
    manifest = {
        "name": "recalls",
        "version": "0.1.0",
        "summary": (
            "Patient recalls: schedule call-backs, work the monthly call "
            "list, log attempts, auto-link booked appointments."
        ),
        "author": "DentalPin Core Team",
        "license": "BSL-1.1",
        "category": "official",
        "depends": ["patients", "agenda"],
        "installable": True,
        "auto_install": True,
        "removable": True,
        "role_permissions": {
            "admin": ["*"],
            "dentist": ["recalls.read", "recalls.write"],
            "hygienist": ["recalls.read", "recalls.write"],
            "assistant": ["recalls.read", "recalls.write"],
            "receptionist": ["recalls.read", "recalls.write"],
        },
        "frontend": {"layer_path": "frontend"},
    }

    def get_models(self) -> list:
        return [Recall, RecallContactAttempt, RecallSettings]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return ["recalls.read", "recalls.write", "recalls.delete"]

    def get_event_handlers(self) -> dict:
        return {
            "appointment.scheduled": on_appointment_scheduled,
            "appointment.completed": on_appointment_completed,
            "appointment.cancelled": on_appointment_cancelled,
            "treatment_plan.treatment_completed": on_treatment_plan_completed,
            "patient.archived": on_patient_archived,
        }

    def get_tools(self) -> list:
        return []
