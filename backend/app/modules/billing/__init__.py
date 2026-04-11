"""Billing module - invoice management and payment tracking."""

from fastapi import APIRouter

from app.core.plugins import BaseModule

from .models import Invoice, InvoiceHistory, InvoiceItem, InvoiceSeries, Payment
from .router import router


class BillingModule(BaseModule):
    """Billing module providing invoice management and payment tracking.

    Features:
    - Invoice creation from budgets or manual
    - Partial invoicing support
    - Multiple payment methods
    - Credit notes (rectificativas)
    - Invoice series with numbering control
    - PDF generation
    - Extensible hooks for country compliance modules
    """

    @property
    def name(self) -> str:
        return "billing"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def dependencies(self) -> list[str]:
        return ["clinical", "catalog", "budget"]

    def get_models(self) -> list:
        return [InvoiceSeries, Invoice, InvoiceItem, Payment, InvoiceHistory]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return [
            "read",  # View invoices
            "write",  # Create/update invoices, record payments
            "admin",  # Manage series, settings, void invoices
        ]

    def get_event_handlers(self) -> dict:
        from .service import InvoiceService

        return {
            "budget.completed": InvoiceService.on_budget_completed,
        }
