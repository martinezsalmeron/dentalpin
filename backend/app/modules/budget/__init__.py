"""Budget module - dental treatment quotes management."""

from fastapi import APIRouter

from app.core.plugins import BaseModule

from .models import Budget, BudgetHistory, BudgetItem, BudgetSignature
from .router import router


class BudgetModule(BaseModule):
    """Budget module providing dental treatment quotes management.

    Features:
    - Budget creation with items from treatment catalog
    - Versioning and duplication
    - Partial acceptance with digital signatures
    - PDF generation
    - Integration with odontogram treatments
    """

    @property
    def name(self) -> str:
        return "budget"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def dependencies(self) -> list[str]:
        return ["clinical", "catalog"]  # Requires patients and catalog

    def get_models(self) -> list:
        return [Budget, BudgetItem, BudgetSignature, BudgetHistory]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return [
            "read",  # View budgets
            "write",  # Create/update budgets
            "admin",  # Delete budgets, manage settings
        ]

    def get_event_handlers(self) -> dict:
        from .service import BudgetService

        return {
            "odontogram.treatment.performed": BudgetService.on_treatment_performed,
        }
