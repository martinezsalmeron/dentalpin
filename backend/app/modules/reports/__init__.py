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

    manifest = {
        "name": "reports",
        "version": "0.1.0",
        "summary": "Cross-module reporting: billing, budgets, scheduling.",
        "author": "DentalPin Core Team",
        "license": "BSL-1.1",
        "category": "official",
        "depends": ["patients", "agenda", "catalog", "budget", "billing", "payments"],
        "installable": True,
        "auto_install": True,
        "removable": False,
        "role_permissions": {
            "admin": ["*"],
            "dentist": ["billing.read", "scheduling.read"],
            "hygienist": ["scheduling.read"],
            "assistant": ["scheduling.read"],
            "receptionist": ["billing.read", "scheduling.read"],
        },
        "frontend": {
            "layer_path": "frontend",
            "navigation": [
                {
                    "label": "nav.reports",
                    "icon": "i-lucide-bar-chart-3",
                    "to": "/reports",
                    "permission": "reports.billing.read",
                    "order": 60,
                },
            ],
        },
    }

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
