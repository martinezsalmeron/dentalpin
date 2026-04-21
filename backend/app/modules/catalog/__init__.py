"""Catalog module - treatment catalog management."""

from fastapi import APIRouter

from app.core.plugins import BaseModule

from .models import TreatmentCatalogItem, TreatmentCategory, TreatmentOdontogramMapping
from .router import router


class CatalogModule(BaseModule):
    """Catalog module providing treatment catalog management.

    This module serves as the foundation for DentalPin's revenue workflow:
    Catalog → Budgets → Billing.

    MVP Features:
    - Internal codes (clinic's own treatment codes)
    - Single price list (default prices per treatment)
    - VAT handling (healthcare exempt vs cosmetic taxable)
    - Duration tracking (for appointment scheduling)
    - Material references (placeholder for future inventory)
    - Odontogram integration (visual treatment mapping)
    """

    manifest = {
        "name": "catalog",
        "version": "0.1.0",
        "summary": "Treatment catalog, categories, VAT types.",
        "author": "DentalPin Core Team",
        "license": "BSL-1.1",
        "category": "official",
        "depends": [],
        "installable": True,
        "auto_install": True,
        "removable": False,
        "role_permissions": {
            "admin": ["*"],
            "dentist": ["read"],
            "hygienist": ["read"],
            "assistant": ["read"],
            "receptionist": ["read"],
        },
        "frontend": {
            "layer_path": "frontend",
        },
    }

    def get_models(self) -> list:
        return [TreatmentCategory, TreatmentCatalogItem, TreatmentOdontogramMapping]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return [
            "read",  # View catalog items
            "write",  # Create/update catalog items
            "admin",  # Manage categories, bulk operations
        ]

    def get_tools(self) -> list:
        return []
