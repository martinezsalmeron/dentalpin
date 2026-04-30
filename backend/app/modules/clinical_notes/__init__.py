"""Clinical notes module — administrative + diagnosis + treatment + plan notes.

Owns the polymorphic ``clinical_notes`` and ``clinical_note_attachments``
tables. Notes attach to one of:

- ``patient``    → administrative or diagnosis notes
- ``treatment``  → per-treatment notes (live with the underlying odontogram
  ``Treatment`` row, so they survive across diagnosis → plan → completion)
- ``plan``       → plan-level (whole treatment plan) notes

UI surfaces (Summary tab feed, diagnosis sidebar, per-row note button,
plan timeline) are mounted via the slot registry — host modules
(``patients``, ``odontogram``, ``treatment_plan``) only expose slot points
and never import this module's services. Backend reads from those modules
go through the explicit ``manifest.depends`` declaration.
"""

from typing import Any

from fastapi import APIRouter

from app.core.plugins import BaseModule

from .models import ClinicalNote, ClinicalNoteAttachment
from .router import router


class ClinicalNotesModule(BaseModule):
    manifest = {
        "name": "clinical_notes",
        "version": "0.1.0",
        "summary": (
            "Polymorphic clinical notes (administrative, diagnosis, treatment, "
            "treatment plan) with author + attachments."
        ),
        "author": "DentalPin Core Team",
        "license": "BSL-1.1",
        "category": "official",
        "depends": ["patients", "odontogram", "treatment_plan", "media"],
        "installable": True,
        "auto_install": True,
        "removable": False,
        "role_permissions": {
            "admin": ["*"],
            "dentist": ["notes.read", "notes.write"],
            "hygienist": ["notes.read", "notes.write"],
            "assistant": ["notes.read", "notes.write"],
            "receptionist": ["notes.read", "notes.write"],
        },
        "frontend": {
            "layer_path": "frontend",
            "navigation": [],
        },
    }

    def get_models(self) -> list:
        return [ClinicalNote, ClinicalNoteAttachment]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return ["notes.read", "notes.write"]

    def get_event_handlers(self) -> dict[str, Any]:
        return {}
