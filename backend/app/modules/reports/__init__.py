"""Reports module - centralized reporting across all domains."""

from fastapi import APIRouter

from app.core.plugins import BaseModule

from .router import router


class ReportsModule(BaseModule):
    """Reports module providing unified reporting across budgets, scheduling, and billing.

    Features:
    - Billing reports (revenue, payments, VAT, overdue)
    - Budget reports (coming soon)
    - Scheduling reports (coming soon)
    - Export functionality (CSV)
    """

    @property
    def name(self) -> str:
        return "reports"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def dependencies(self) -> list[str]:
        return ["clinical", "catalog", "budget", "billing"]

    def get_models(self) -> list:
        # Reports module has no models - it queries other modules' data
        return []

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return [
            "billing.read",  # View billing reports
            "budgets.read",  # View budget reports
            "scheduling.read",  # View scheduling reports
        ]
