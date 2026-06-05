"""Agent tools for the payments module.

Thin wrappers over ``PaymentReportsService`` — no business logic here.
Clinic-scoped; RBAC via the existing ``payments.reports.read``.

**Off-books boundary (project rule):** these tools expose the *collection
axis only* (gross collected / refunded). They deliberately drop the
receivable / patient-credit figures from the underlying summary, because
"what is still owed" equals the invoiced-minus-collected difference that
clinics keep off-record. The invoice axis lives in ``reports/tools.py``;
the copilot system prompt forbids surfacing the difference between them.
"""

from __future__ import annotations

from datetime import date as date_cls

from pydantic import BaseModel, Field
from sqlalchemy import select

from app.core.agents import AgentContext, Tool, ToolCategory
from app.core.auth.models import Clinic

from .service import PaymentReportsService


class PeriodArgs(BaseModel):
    date_from: date_cls = Field(description="Inicio del periodo (YYYY-MM-DD).")
    date_to: date_cls = Field(description="Fin del periodo (YYYY-MM-DD).")


async def _currency(ctx: AgentContext) -> str:
    return (await ctx.db.scalar(select(Clinic.currency).where(Clinic.id == ctx.clinic_id))) or "EUR"


async def _payments_summary(ctx: AgentContext, params: PeriodArgs) -> dict:
    currency = await _currency(ctx)
    s = await PaymentReportsService.summary(
        ctx.db, ctx.clinic_id, currency, params.date_from, params.date_to
    )
    # Collection axis only — drop patient_credit_total / clinic_receivable_total.
    return {
        "date_from": params.date_from,
        "date_to": params.date_to,
        "currency": s.currency,
        "total_collected": s.total_collected,
        "total_refunded": s.total_refunded,
        "net_collected": s.net_collected,
        "payment_count": s.payment_count,
        "refund_count": s.refund_count,
    }


async def _collections_by_method(ctx: AgentContext, params: PeriodArgs) -> dict:
    rows = await PaymentReportsService.by_method(
        ctx.db, ctx.clinic_id, params.date_from, params.date_to
    )
    return {"methods": [{"method": r.method, "total": r.total, "count": r.count} for r in rows]}


def get_tools() -> list[Tool]:
    return [
        Tool(
            name="payments_summary",
            description=(
                "Resumen de cobros de un periodo: cobrado, devuelto y neto. "
                "Solo eje cobro (no incluye facturación ni saldo pendiente)."
            ),
            parameters=PeriodArgs,
            handler=_payments_summary,
            permissions=["payments.reports.read"],
            category=ToolCategory.READ,
        ),
        Tool(
            name="collections_by_method",
            description="Desglose de lo cobrado por método de pago en un periodo (eje cobro).",
            parameters=PeriodArgs,
            handler=_collections_by_method,
            permissions=["payments.reports.read"],
            category=ToolCategory.READ,
        ),
    ]
