"""Payments module — patient-centric collections, allocations, refunds.

Owns the full payment lifecycle outside billing. A ``Payment`` belongs
to a patient and is split across one or more ``PaymentAllocation``
rows (target ``budget`` or ``on_account``). The link between a payment
and an invoice lives in the billing module (``InvoicePayment``) — that
direction respects the dependency graph (``billing.depends`` includes
``payments``; the reverse is forbidden).

The "earned" signal that powers patient-credit / receivable metrics
is computed from a denormalized ledger ``PatientEarnedEntry``,
populated by event handlers reacting to ``odontogram.treatment.performed``
and ``treatment_plan.treatment_completed``. No imports of those modules.

Refunds are first-class — there is no ``is_voided`` flag. A full reverso
is just ``Refund(amount=Payment.amount)``.
"""

from fastapi import APIRouter

from app.core.events import EventType
from app.core.plugins import BaseModule

from .events import on_plan_item_completed, on_treatment_performed
from .models import (
    PatientEarnedEntry,
    Payment,
    PaymentAllocation,
    PaymentHistory,
    Refund,
)
from .router import router


class PaymentsModule(BaseModule):
    manifest = {
        "name": "payments",
        "version": "0.1.0",
        "summary": (
            "Patient-centric collections, allocations to budgets / on-account, "
            "refunds, patient ledger, and dental payment reports."
        ),
        "author": "DentalPin Core Team",
        "license": "BSL-1.1",
        "category": "official",
        "depends": ["patients", "budget"],
        "installable": True,
        "auto_install": True,
        "removable": False,
        "role_permissions": {
            "admin": ["*"],
            "dentist": ["record.read", "record.write", "record.refund", "reports.read"],
            # Clinical-only roles don't see payment reports — they touch the
            # ledger from the patient screen, not from the dashboards.
            "hygienist": ["record.read"],
            "assistant": ["record.read", "record.write"],
            "receptionist": ["record.read", "record.write", "reports.read"],
        },
        "frontend": {
            "layer_path": "frontend",
            "navigation": [
                {
                    "label": "payments.nav.payments",
                    "icon": "i-lucide-wallet",
                    "to": "/payments",
                    "permission": "payments.record.read",
                    "order": 55,
                },
            ],
        },
    }

    def get_models(self) -> list:
        return [Payment, PaymentAllocation, Refund, PatientEarnedEntry, PaymentHistory]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return ["record.read", "record.write", "record.refund", "reports.read"]

    def get_event_handlers(self) -> dict:
        return {
            EventType.ODONTOGRAM_TREATMENT_PERFORMED: on_treatment_performed,
            EventType.TREATMENT_PLAN_TREATMENT_COMPLETED: on_plan_item_completed,
        }
