"""Accounting export module — gestoría hand-off of invoices + payments.

Optional, removable, model-free. Exports issued invoices and the
payments allocated to them as downloadable CSV files for the clinic's
accountant. Reads billing/payments data via their service APIs only —
no cross-module model imports, no own tables.
"""

from fastapi import APIRouter

from app.core.plugins import BaseModule

from .router import router


class AccountingExportModule(BaseModule):
    """Exports billing data in accountant-consumable formats."""

    manifest = {
        "name": "accounting_export",
        "version": "0.1.0",
        "summary": "Export invoices and payments for the accountant (gestoría).",
        "author": "DentalPin Core Team",
        "license": "BSL-1.1",
        "category": "official",
        "depends": ["billing", "payments"],
        "installable": True,
        "auto_install": False,
        "removable": True,
        "role_permissions": {
            # Admin-only: fiscal hand-off is an admin concern.
            "admin": ["*"],
        },
        "frontend": {
            "layer_path": "frontend",
            "navigation": [
                {
                    "label": "nav.accountingExport",
                    "icon": "i-lucide-file-spreadsheet",
                    "to": "/accounting-export",
                    "permission": "accounting_export.export.read",
                    "order": 70,
                },
            ],
        },
    }

    def get_models(self) -> list:
        # Stateless export — no own tables, so uninstall never touches
        # the schema and the round-trip is trivial.
        return []

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return ["export.read", "export.run"]
