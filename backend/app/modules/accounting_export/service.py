"""Accounting export service — gestoría-ready rows + CSV/ZIP files.

Invoice-centric by design: only issued invoices and the payments
**allocated to them** (``InvoicePayment``) are exported. The raw payment
ledger is never surfaced — the off-books boundary (ADR 0010) forbids
juxtaposing the collection axis against the invoice axis. A cash payment
not tied to any invoice simply does not appear here.

Data is read through billing's service API (``InvoiceService``); this
module imports no billing/payments models and owns no tables.
"""

from __future__ import annotations

import csv
import io
import zipfile
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.billing.service import InvoiceService

# Non-draft statuses are the export universe. Drafts are not fiscal
# documents and never leave the clinic.
EXPORTABLE_STATUSES = ["issued", "partial", "paid", "cancelled", "voided"]

INVOICE_HEADERS = [
    "numero",
    "serie",
    "fecha_emision",
    "cliente",
    "nif",
    "base",
    "tipo_iva",
    "cuota_iva",
    "total",
    "estado",
]
PAYMENT_HEADERS = ["fecha_pago", "factura", "importe", "metodo", "referencia"]


def _vat_rate(invoice) -> str:
    """Single rate as ``21``/``10``; ``varios`` when the invoice mixes rates."""
    rates = {item.vat_rate for item in invoice.items}
    if len(rates) == 1:
        return f"{next(iter(rates)):g}"
    return "varios"


class AccountingExportService:
    @staticmethod
    async def fetch(
        db: AsyncSession,
        clinic_id: UUID,
        date_from: date | None,
        date_to: date | None,
        statuses: list[str] | None,
    ) -> list:
        """Issued invoices with items + allocated payments eager-loaded."""
        return await InvoiceService.list_for_export(
            db,
            clinic_id,
            date_from=date_from,
            date_to=date_to,
            statuses=statuses,
        )

    @staticmethod
    def invoice_rows(invoices: list) -> list[dict]:
        rows: list[dict] = []
        for inv in invoices:
            rows.append(
                {
                    "numero": inv.invoice_number or "",
                    "serie": inv.series.prefix if inv.series else "",
                    "fecha_emision": inv.issue_date.isoformat() if inv.issue_date else "",
                    "cliente": inv.billing_name or "",
                    "nif": inv.billing_tax_id or "",
                    # Taxable base = pre-tax subtotal minus discounts.
                    "base": inv.subtotal - inv.total_discount,
                    "tipo_iva": _vat_rate(inv),
                    "cuota_iva": inv.total_tax,
                    "total": inv.total,
                    "estado": inv.status,
                }
            )
        return rows

    @staticmethod
    def payment_rows(invoices: list) -> list[dict]:
        """One row per invoice↔payment allocation (off-books safe)."""
        rows: list[dict] = []
        for inv in invoices:
            for ip in inv.invoice_payments:
                p = ip.payment
                rows.append(
                    {
                        "fecha_pago": p.payment_date.isoformat() if p and p.payment_date else "",
                        "factura": inv.invoice_number or "",
                        "importe": ip.amount,
                        "metodo": p.method if p else "",
                        "referencia": (p.reference if p else "") or "",
                    }
                )
        return rows

    @staticmethod
    def totals(rows: list[dict]) -> tuple[Decimal, Decimal, Decimal]:
        """(base, cuota, total) sums for the invoice preview."""
        base = sum((r["base"] for r in rows), Decimal("0.00"))
        cuota = sum((r["cuota_iva"] for r in rows), Decimal("0.00"))
        total = sum((r["total"] for r in rows), Decimal("0.00"))
        return base, cuota, total

    @staticmethod
    def build_zip(invoices: list, separator: str = ",") -> bytes:
        inv_csv = to_csv(AccountingExportService.invoice_rows(invoices), INVOICE_HEADERS, separator)
        pay_csv = to_csv(AccountingExportService.payment_rows(invoices), PAYMENT_HEADERS, separator)
        return to_zip({"facturas.csv": inv_csv, "cobros.csv": pay_csv})


def _fmt(value, separator: str) -> str:
    if isinstance(value, Decimal):
        s = f"{value:.2f}"
        # Spanish Excel pairs ";" with comma decimals; "," with dot.
        return s.replace(".", ",") if separator == ";" else s
    return "" if value is None else str(value)


def to_csv(rows: list[dict], headers: list[str], separator: str = ",") -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=separator)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([_fmt(row[h], separator) for h in headers])
    # UTF-8 BOM so Excel-ES detects the encoding and renders accents.
    return b"\xef\xbb\xbf" + buf.getvalue().encode("utf-8")


def to_zip(files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buf.getvalue()
