"""India GST module — CGST/SGST/IGST billing compliance for India.

Extends the billing module via the ``BillingComplianceHook`` registry,
exactly like ``verifactu`` (Spain/AEAT); never imports billing internals
directly. Country-gated: inactive (and invisible) for clinics whose
``clinic.settings['country'] != 'IN'``.

Manual install only (``auto_install=False``). E-invoice in v1 only
tracks applicability per invoice (``not_required``/``not_configured``);
there is no GSP/IRP provider integration — retry always answers 409.
"""

from fastapi import APIRouter

from app.core.plugins import BaseModule

from .models import (
    IndiaGstCatalogItem,
    IndiaGstDocumentSequence,
    IndiaGstEinvoiceSubmission,
    IndiaGstInvoiceItem,
    IndiaGstSettings,
)
from .router import router


class IndiaGstModule(BaseModule):
    manifest = {
        "name": "india_gst",
        "version": "0.1.0",
        "summary": "CGST/SGST/IGST GST billing compliance for Indian clinics.",
        "author": "tresundios",
        "license": "BSL-1.1",
        "category": "official",
        "depends": ["billing", "catalog"],
        "installable": True,
        "auto_install": False,
        "removable": True,
        "role_permissions": {
            "admin": ["*"],
            # settings.read gates the read-only endpoints the invoice
            # form/detail panels call (tax-preview, e-invoice status) —
            # every role that can touch invoices needs it or the panel
            # 403s mid-invoicing.
            "dentist": ["reports.read", "settings.read"],
            "hygienist": ["settings.read"],
            "assistant": ["settings.read"],
            "receptionist": ["reports.read", "settings.read"],
        },
        "frontend": {
            "layer_path": "frontend",
            "navigation": [
                {
                    "label": "nav.indiaGst",
                    "icon": "i-lucide-receipt-indian-rupee",
                    "to": "/reports/india-gst",
                    "permission": "india_gst.reports.read",
                    "order": 71,
                },
            ],
        },
    }

    def __init__(self) -> None:
        # Register the BillingComplianceHook on every backend boot — the
        # one-time ``install`` lifecycle only runs when the user clicks
        # Install in the admin UI; subsequent restarts wipe the
        # in-memory registry, so hooks must be re-attached at module
        # load time. Idempotent: BillingHookRegistry keys by
        # country_code. Mirrors verifactu/__init__.py exactly.
        from app.modules.billing.hooks import BillingHookRegistry

        from .hook import IndiaGstHook

        BillingHookRegistry.register(IndiaGstHook())

    def get_models(self) -> list:
        return [
            IndiaGstSettings,
            IndiaGstCatalogItem,
            IndiaGstInvoiceItem,
            IndiaGstDocumentSequence,
            IndiaGstEinvoiceSubmission,
        ]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return [
            "settings.read",
            "settings.configure",
            "catalog.manage",
            "reports.read",
        ]

    def get_event_handlers(self) -> dict:
        return {}

    def get_tools(self) -> list:
        from .tools import get_tools

        return get_tools()

    async def install(self, ctx) -> None:
        from app.modules.billing.hooks import BillingHookRegistry

        from .hook import IndiaGstHook

        BillingHookRegistry.register(IndiaGstHook())
        ctx.logger.info("india_gst hook registered for country=IN")

    async def uninstall(self, ctx) -> None:
        from sqlalchemy import func, select

        from app.modules.billing.hooks import BillingHookRegistry
        from app.modules.billing.models import Invoice, InvoiceItem

        from .models import IndiaGstInvoiceItem

        # Guard: refuse uninstall if any non-draft invoice has GST line-item
        # data.  Removing the module would orphan the CGST/SGST/IGST
        # breakdown that was already communicated to the customer.
        gst_invoice_q = await ctx.db.execute(
            select(func.count())
            .select_from(IndiaGstInvoiceItem)
            .join(
                InvoiceItem,
                IndiaGstInvoiceItem.invoice_item_id == InvoiceItem.id,
            )
            .join(Invoice, Invoice.id == InvoiceItem.invoice_id)
            .where(Invoice.status != "draft")
        )
        issued_gst_count = gst_invoice_q.scalar() or 0
        if issued_gst_count > 0:
            raise RuntimeError(
                f"Cannot uninstall india_gst: {issued_gst_count} line items on "
                f"issued invoices still have GST data. "
                f"Void or credit-note those invoices first."
            )

        BillingHookRegistry.unregister("IN")
        ctx.logger.info("india_gst hook unregistered")
