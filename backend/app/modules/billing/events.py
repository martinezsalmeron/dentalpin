"""Billing event handlers.

Currently only consumes ``payment.refunded`` to recompute the status of
any invoices whose ``invoice_payments`` link the refunded Payment —
``paid → partial`` or ``partial → issued`` happen here rather than
inside payments (which has no view of invoices).
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select

from app.database import async_session_maker

from .models import Invoice, InvoicePayment
from .workflow import InvoiceWorkflowService

logger = logging.getLogger(__name__)


async def on_payment_refunded(data: dict[str, Any]) -> None:
    """Refund happened upstream — re-evaluate any invoice the payment
    was imputed against.

    Idempotent: ``recalc_invoice_status`` is a no-op when status
    matches reality.
    """
    payment_id_raw = data.get("payment_id")
    clinic_id_raw = data.get("clinic_id")
    if not payment_id_raw or not clinic_id_raw:
        return

    try:
        payment_id = UUID(str(payment_id_raw))
        clinic_id = UUID(str(clinic_id_raw))
    except (ValueError, TypeError):
        return

    async with async_session_maker() as db:
        try:
            invoice_ids_q = await db.execute(
                select(InvoicePayment.invoice_id)
                .where(
                    InvoicePayment.payment_id == payment_id,
                    InvoicePayment.clinic_id == clinic_id,
                )
                .distinct()
            )
            invoice_ids = [row[0] for row in invoice_ids_q.all()]
            if not invoice_ids:
                return

            invoices_q = await db.execute(select(Invoice).where(Invoice.id.in_(invoice_ids)))
            for invoice in invoices_q.scalars():
                # Re-evaluate status from current invoice_payments + refunds.
                # The "actor" here is the user who triggered the refund.
                refunded_by = data.get("refunded_by")
                actor_id = (
                    UUID(str(refunded_by))
                    if refunded_by
                    else invoice.created_by  # fall back to invoice creator
                )
                await InvoiceWorkflowService.recalc_invoice_status(db, invoice, actor_id=actor_id)
            await db.commit()
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("billing.on_payment_refunded failed: %s", exc, exc_info=True)
            await db.rollback()
