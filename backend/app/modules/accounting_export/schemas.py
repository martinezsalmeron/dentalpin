"""Accounting export schemas."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel


class ExportPreview(BaseModel):
    """Counts, totals and a sample of rows for the UI preview."""

    invoice_count: int
    payment_count: int
    total_base: Decimal
    total_cuota: Decimal
    total: Decimal
    sample_invoices: list[dict]
    sample_payments: list[dict]
