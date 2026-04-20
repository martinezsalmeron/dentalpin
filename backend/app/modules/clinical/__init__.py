"""Clinical module — remaining shell for dashboard + settings nav.

All domain ownership moved out during Fase B:

* Patient identity → ``patients``
* Appointments + cabinets → ``agenda``
* Timeline + its event handlers → ``patient_timeline``

What's left here is a thin package hosting:

* ``/api/v1/clinical/clinics`` endpoints (clinic metadata management).
* The dashboard + settings nav entries in the host shell.
* Convenience re-exports (models, schemas, services) for legacy
  imports during the Fase B transition. Every re-export is a signal
  that a caller should migrate to the real owning module.
"""

from fastapi import APIRouter

from app.core.plugins import BaseModule

from .router import router


class ClinicalModule(BaseModule):
    """Clinic metadata + host navigation shell."""

    manifest = {
        "name": "clinical",
        "version": "0.3.0",
        "summary": "Clinic metadata endpoints + host nav shell.",
        "author": "DentalPin Core Team",
        "license": "BSL-1.1",
        "category": "official",
        "depends": ["patients", "agenda", "patient_timeline"],
        "installable": True,
        "auto_install": True,
        "removable": False,
        "role_permissions": {
            "admin": ["*"],
        },
        "frontend": {
            "navigation": [
                {
                    "label": "nav.dashboard",
                    "icon": "i-lucide-home",
                    "to": "/",
                    "order": 0,
                },
                {
                    "label": "nav.settings",
                    "icon": "i-lucide-settings",
                    "to": "/settings",
                    "order": 900,
                },
            ],
        },
    }

    def get_models(self) -> list:
        # All models moved out in Fase B.
        return []

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return []
