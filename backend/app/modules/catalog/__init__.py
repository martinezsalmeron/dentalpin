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

    @property
    def name(self) -> str:
        return "catalog"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def dependencies(self) -> list[str]:
        return []  # No dependencies for MVP

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
