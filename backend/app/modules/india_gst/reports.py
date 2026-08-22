"""GST transaction/reconciliation reports and export.

Explicitly a reconciliation aid, not a validated statutory GSTR-1
filing artifact. Reads through billing's ``InvoiceService`` only — no
new billing model imports, mirrors the ``accounting_export`` module's
CSV pattern (stdlib ``csv``, no new dependency).

Scope: issued/partial/paid invoices and credit notes. Drafts and
cancelled invoices are excluded from totals.
"""

from __future__ import annotations

import csv
import io
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .constants import state_name
from .models import IndiaGstInvoiceItem
from .schemas import GstReportSummaryResponse, GstReportTransactionRow

REPORTABLE_STATUSES = ("issued", "partial", "paid")

CSV_HEADERS = [
    "invoice_date",
    "gst_document_number",
    "recipient_gstin",
    "place_of_supply",
    "taxable_value",
    "cgst",
    "sgst",
    "igst",
    "status",
    "is_credit_note",
]


def _invoice_conditions(clinic_id: UUID, date_from: date | None, date_to: date | None) -> list:
    from app.modules.billing.models import Invoice

    conditions = [
        Invoice.clinic_id == clinic_id,
        Invoice.deleted_at.is_(None),
        Invoice.status.in_(REPORTABLE_STATUSES),
    ]
    if date_from:
        conditions.append(Invoice.issue_date >= date_from)
    if date_to:
        conditions.append(Invoice.issue_date <= date_to)
    return conditions


async def _fetch_invoices(
    db: AsyncSession,
    clinic_id: UUID,
    *,
    date_from: date | None,
    date_to: date | None,
    page: int | None = None,
    page_size: int | None = None,
) -> list:
    from app.modules.billing.models import Invoice

    query = (
        select(Invoice)
        .where(*_invoice_conditions(clinic_id, date_from, date_to))
        .options(selectinload(Invoice.items))
        .order_by(Invoice.issue_date)
    )
    if page is not None and page_size is not None:
        query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return list(result.scalars().unique().all())


async def _count_invoices(
    db: AsyncSession, clinic_id: UUID, *, date_from: date | None, date_to: date | None
) -> int:
    from app.modules.billing.models import Invoice

    result = await db.execute(
        select(func.count())
        .select_from(Invoice)
        .where(*_invoice_conditions(clinic_id, date_from, date_to))
    )
    return result.scalar() or 0


async def _gst_rows_for_items(
    db: AsyncSession, clinic_id: UUID, invoice_item_ids: list[UUID]
) -> dict:
    if not invoice_item_ids:
        return {}
    result = await db.execute(
        select(IndiaGstInvoiceItem).where(
            IndiaGstInvoiceItem.clinic_id == clinic_id,
            IndiaGstInvoiceItem.invoice_item_id.in_(invoice_item_ids),
        )
    )
    return {row.invoice_item_id: row for row in result.scalars()}


async def _transaction_rows(
    db: AsyncSession,
    clinic_id: UUID,
    *,
    date_from: date | None,
    date_to: date | None,
    page: int | None = None,
    page_size: int | None = None,
) -> list[GstReportTransactionRow]:
    invoices = await _fetch_invoices(
        db, clinic_id, date_from=date_from, date_to=date_to, page=page, page_size=page_size
    )
    all_item_ids = [item.id for inv in invoices for item in inv.items]
    gst_by_item = await _gst_rows_for_items(db, clinic_id, all_item_ids)

    rows: list[GstReportTransactionRow] = []
    for inv in invoices:
        cgst = sgst = igst = taxable = Decimal("0")
        for item in inv.items:
            gst_row = gst_by_item.get(item.id)
            if gst_row is None:
                continue
            cgst += gst_row.cgst_amount
            sgst += gst_row.sgst_amount
            igst += gst_row.igst_amount
            taxable += item.line_subtotal - item.line_discount
        cd = (inv.compliance_data or {}).get("IN") or {}
        rows.append(
            GstReportTransactionRow(
                invoice_id=inv.id,
                gst_document_number=cd.get("gst_document_number"),
                issue_date=inv.issue_date.isoformat() if inv.issue_date else None,
                recipient_gstin=inv.billing_tax_id,
                place_of_supply=cd.get("place_of_supply"),
                taxable_value=taxable,
                cgst=cgst,
                sgst=sgst,
                igst=igst,
                status=inv.status,
                is_credit_note=inv.credit_note_for_id is not None,
            )
        )
    return rows


async def build_summary(
    db: AsyncSession, clinic_id: UUID, *, date_from: date | None, date_to: date | None
) -> GstReportSummaryResponse:
    rows = await _transaction_rows(db, clinic_id, date_from=date_from, date_to=date_to)

    cgst_total = sum((r.cgst for r in rows), Decimal("0"))
    sgst_total = sum((r.sgst for r in rows), Decimal("0"))
    igst_total = sum((r.igst for r in rows), Decimal("0"))
    invoice_count = sum(1 for r in rows if not r.is_credit_note)
    credit_note_count = sum(1 for r in rows if r.is_credit_note)

    by_state: dict[str | None, dict] = {}
    for r in rows:
        bucket = by_state.setdefault(
            r.place_of_supply, {"cgst": Decimal("0"), "sgst": Decimal("0"), "igst": Decimal("0")}
        )
        bucket["cgst"] += r.cgst
        bucket["sgst"] += r.sgst
        bucket["igst"] += r.igst

    by_place_of_supply = [
        {
            "state_code": code,
            "state_name": state_name(code),
            "cgst": str(v["cgst"]),
            "sgst": str(v["sgst"]),
            "igst": str(v["igst"]),
        }
        for code, v in by_state.items()
    ]

    return GstReportSummaryResponse(
        cgst_total=cgst_total,
        sgst_total=sgst_total,
        igst_total=igst_total,
        invoice_count=invoice_count,
        credit_note_count=credit_note_count,
        by_place_of_supply=by_place_of_supply,
    )


async def list_transactions(
    db: AsyncSession,
    clinic_id: UUID,
    *,
    date_from: date | None,
    date_to: date | None,
    page: int,
    page_size: int,
) -> tuple[list[GstReportTransactionRow], int]:
    """One row per invoice, paginated in SQL. Returns ``(rows, total)``."""
    total = await _count_invoices(db, clinic_id, date_from=date_from, date_to=date_to)
    rows = await _transaction_rows(
        db, clinic_id, date_from=date_from, date_to=date_to, page=page, page_size=page_size
    )
    return rows, total


def _csv_cell(value: str) -> str:
    """Neutralize spreadsheet formula injection: Excel/Sheets execute
    cells starting with = + - @ (or tab/CR). Values here include
    user-entered GSTINs and document prefixes, so prefix a ``'``.
    """
    if value and value[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{value}"
    return value


async def build_export_csv(
    db: AsyncSession, clinic_id: UUID, *, date_from: date | None, date_to: date | None
) -> bytes:
    rows = await _transaction_rows(db, clinic_id, date_from=date_from, date_to=date_to)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(CSV_HEADERS)
    for r in rows:
        # _csv_cell only on free-text columns — numeric columns start
        # with a legitimate "-" for credit notes.
        writer.writerow(
            [
                r.issue_date or "",
                _csv_cell(r.gst_document_number or ""),
                _csv_cell(r.recipient_gstin or ""),
                _csv_cell(r.place_of_supply or ""),
                f"{r.taxable_value:.2f}",
                f"{r.cgst:.2f}",
                f"{r.sgst:.2f}",
                f"{r.igst:.2f}",
                _csv_cell(r.status),
                "yes" if r.is_credit_note else "no",
            ]
        )
    return buf.getvalue().encode("utf-8")
