"""Verifactu (AEAT) compliance module — Spain.

Implements the RRSIF / Veri*Factu spec (RD 1007/2023, Orden HAC/1177/2024)
mandatory for Spanish clinics from 2027. Extends the billing module via
the ``BillingComplianceHook`` registry; never imports billing internals
directly.

Manual install only (``auto_install=False``). Becomes irreversible once
fiscal records are sent to AEAT (uninstall blocks).
"""

from fastapi import APIRouter

from app.core.plugins import BaseModule

from .models import (
    VerifactuCertificate,
    VerifactuRecord,
    VerifactuSettings,
    VerifactuVatClassification,
)
from .router import router


class VerifactuModule(BaseModule):
    manifest = {
        "name": "verifactu",
        "version": "0.1.0",
        "summary": "Cumplimiento Veri*Factu (AEAT) para clínicas en España.",
        "author": "DentalPin Core Team",
        "license": "BSL-1.1",
        "category": "official",
        "depends": ["billing", "catalog"],
        "installable": True,
        "auto_install": False,
        "removable": True,
        "role_permissions": {
            "admin": ["*"],
            "dentist": ["records.read"],
            "hygienist": [],
            "assistant": [],
            "receptionist": ["records.read"],
        },
        "frontend": {
            "layer_path": "frontend",
        },
    }

    def __init__(self) -> None:
        # Register the BillingComplianceHook on every backend boot — the
        # one-time ``install`` lifecycle only runs when the user clicks
        # Install in the admin UI; subsequent restarts wipe the in-memory
        # registry, so hooks must be re-attached at module load time.
        # Idempotent: ``BillingHookRegistry`` keys by country_code.
        from app.modules.billing.hooks import BillingHookRegistry

        from .hook import VerifactuHook
        from .tasks import register_event_handlers

        BillingHookRegistry.register(VerifactuHook())
        # Same reasoning for the event bus subscription — re-attach on
        # boot so the rejected-record email handler survives restarts.
        register_event_handlers()

    def get_models(self) -> list:
        return [
            VerifactuSettings,
            VerifactuCertificate,
            VerifactuRecord,
            VerifactuVatClassification,
        ]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return [
            "settings.read",
            "settings.configure",
            "records.read",
            "queue.manage",
            "environment.promote",
        ]

    def get_event_handlers(self) -> dict:
        from .events import on_invoice_paid

        return {
            "invoice.paid": on_invoice_paid,
        }

    def get_tools(self) -> list:
        return []

    async def install(self, ctx) -> None:
        from sqlalchemy import select

        from app.modules.billing.hooks import BillingHookRegistry
        from app.modules.catalog.models import VatType

        from .hook import VerifactuHook
        from .tasks import register_jobs

        BillingHookRegistry.register(VerifactuHook())
        register_jobs()
        ctx.logger.info("verifactu hook registered for country=ES")

        # Seed default AEAT classification for every existing
        # zero-rated VAT type. For dental clinics, rate=0 typically
        # means "exento sanitario art. 20.uno.3.º LIVA" → ``E1``. The
        # admin can later override this from the verifactu config
        # panel. Idempotent: only inserts when no override exists yet.
        zero_rates = await ctx.db.execute(
            select(VatType.id, VatType.clinic_id).where(VatType.rate == 0)
        )
        for vat_type_id, clinic_id in zero_rates.all():
            existing = await ctx.db.execute(
                select(VerifactuVatClassification.id).where(
                    VerifactuVatClassification.clinic_id == clinic_id,
                    VerifactuVatClassification.vat_type_id == vat_type_id,
                )
            )
            if existing.first() is not None:
                continue
            ctx.db.add(
                VerifactuVatClassification(
                    clinic_id=clinic_id,
                    vat_type_id=vat_type_id,
                    classification="E1",
                    exemption_cause="E1",
                    notes="Servicios sanitarios — art. 20.uno.3.º LIVA (semilla por defecto).",
                )
            )

    async def uninstall(self, ctx) -> None:
        from sqlalchemy import select

        from app.modules.billing.hooks import BillingHookRegistry

        from .models import VerifactuRecord
        from .tasks import unregister_jobs

        result = await ctx.db.execute(
            select(VerifactuRecord.id)
            .where(VerifactuRecord.state.in_(("accepted", "accepted_with_errors")))
            .limit(1)
        )
        if result.first() is not None:
            raise RuntimeError(
                "No se puede desinstalar verifactu: existen registros "
                "fiscales aceptados por la AEAT. La ley exige conservar el "
                "libro de facturación 4 años. Exporta el libro antes de "
                "intentar desinstalar."
            )
        from .tasks import unregister_event_handlers

        BillingHookRegistry.unregister("ES")
        unregister_jobs()
        unregister_event_handlers()
        ctx.logger.info("verifactu hook unregistered")
