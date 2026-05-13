"""Billing report service."""

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.auth.models import User
from app.modules.billing.models import Invoice, InvoiceItem, InvoicePayment, InvoiceSeries
from app.modules.budget.models import Budget
from app.modules.catalog.models import VatType


class BillingReportService:
    """Service for billing reports."""

    @staticmethod
    async def get_patient_summary(
        db: AsyncSession,
        clinic_id: UUID,
        patient_id: UUID,
    ) -> dict[str, Any]:
        """Get billing summary for a specific patient.

        Returns:
            - total_budgeted: Sum of all budgets
            - work_in_progress: Sum of accepted budgets
            - work_completed: Sum of completed budgets
            - total_invoiced: Sum of issued invoices
            - total_paid: Sum of payments
            - balance_pending: total_invoiced - total_paid
        """
        from sqlalchemy import case

        # Budget aggregation
        budget_result = await db.execute(
            select(
                func.coalesce(func.sum(Budget.total), Decimal("0")).label("total_budgeted"),
                func.coalesce(
                    func.sum(case((Budget.status == "accepted", Budget.total), else_=0)),
                    Decimal("0"),
                ).label("work_in_progress"),
                func.coalesce(
                    func.sum(case((Budget.status == "completed", Budget.total), else_=0)),
                    Decimal("0"),
                ).label("work_completed"),
            ).where(
                Budget.clinic_id == clinic_id,
                Budget.patient_id == patient_id,
                Budget.deleted_at.is_(None),
            )
        )
        budget_totals = budget_result.one()

        # Invoice aggregation (only issued, partial, paid). ``total_paid``
        # comes from ``invoice_payments`` since the legacy cached column
        # was removed when payments became its own module.
        invoice_result = await db.execute(
            select(
                func.coalesce(func.sum(Invoice.total), Decimal("0")).label("total_invoiced"),
            ).where(
                Invoice.clinic_id == clinic_id,
                Invoice.patient_id == patient_id,
                Invoice.status.in_(["issued", "partial", "paid"]),
                Invoice.deleted_at.is_(None),
            )
        )
        invoice_totals = invoice_result.one()

        paid_result = await db.execute(
            select(func.coalesce(func.sum(InvoicePayment.amount), Decimal("0")))
            .join(Invoice, Invoice.id == InvoicePayment.invoice_id)
            .where(
                Invoice.clinic_id == clinic_id,
                Invoice.patient_id == patient_id,
                Invoice.status.in_(["issued", "partial", "paid"]),
                Invoice.deleted_at.is_(None),
            )
        )
        total_invoiced = invoice_totals.total_invoiced
        total_paid: Decimal = paid_result.scalar_one()
        balance_pending = total_invoiced - total_paid

        return {
            "patient_id": patient_id,
            "total_budgeted": budget_totals.total_budgeted,
            "work_in_progress": budget_totals.work_in_progress,
            "work_completed": budget_totals.work_completed,
            "total_invoiced": total_invoiced,
            "total_paid": total_paid,
            "balance_pending": balance_pending,
        }

    @staticmethod
    async def get_summary(
        db: AsyncSession,
        clinic_id: UUID,
        date_from: date,
        date_to: date,
    ) -> dict[str, Any]:
        """Get billing summary for a period.

        Returns:
            - total_invoiced: Total amount invoiced (issued invoices in period)
            - total_paid: Total payments received in period
            - total_pending: Total balance due (all outstanding invoices)
            - invoice_count: Number of invoices issued in period
            - paid_count: Number of fully paid invoices in period
            - overdue_count: Number of overdue invoices (all time)
            - vat_breakdown: VAT breakdown by rate
        """
        # Get totals for issued invoices in the period. ``total_pending``
        # is the sum of invoice totals minus their imputed payments.
        result = await db.execute(
            select(
                func.count(Invoice.id).label("invoice_count"),
                func.coalesce(func.sum(Invoice.total), Decimal("0")).label("total_invoiced"),
            ).where(
                Invoice.clinic_id == clinic_id,
                Invoice.status.notin_(["draft", "voided"]),
                Invoice.issue_date >= date_from,
                Invoice.issue_date <= date_to,
                Invoice.deleted_at.is_(None),
            )
        )
        totals = result.one()

        # ``total_pending`` = Σ invoice.total − Σ imputed payments, across
        # all outstanding invoices in the clinic. LEFT JOIN keeps invoices
        # without any payment imputed.
        pending_total = await db.execute(
            select(func.coalesce(func.sum(Invoice.total), Decimal("0"))).where(
                Invoice.clinic_id == clinic_id,
                Invoice.status.in_(["issued", "partial"]),
                Invoice.deleted_at.is_(None),
            )
        )
        pending_paid = await db.execute(
            select(func.coalesce(func.sum(InvoicePayment.amount), Decimal("0")))
            .join(Invoice, Invoice.id == InvoicePayment.invoice_id)
            .where(
                Invoice.clinic_id == clinic_id,
                Invoice.status.in_(["issued", "partial"]),
                Invoice.deleted_at.is_(None),
            )
        )
        total_pending = pending_total.scalar_one() - pending_paid.scalar_one()

        # Total paid in period for billed invoices. Computed from the
        # InvoicePayment link table — this represents the fiscal "cobrado
        # via factura" view (legitimate, fiscal-axis report). The
        # patient-centric "total collected" lives in the payments
        # module's own reports.
        result = await db.execute(
            select(
                func.coalesce(func.sum(InvoicePayment.amount), Decimal("0")).label("total_paid"),
            ).where(
                InvoicePayment.clinic_id == clinic_id,
                InvoicePayment.created_at
                >= datetime.combine(date_from, datetime.min.time(), tzinfo=UTC),
                InvoicePayment.created_at
                <= datetime.combine(date_to, datetime.max.time(), tzinfo=UTC),
            )
        )
        payments_totals = result.one()

        # Count paid invoices
        result = await db.execute(
            select(func.count(Invoice.id)).where(
                Invoice.clinic_id == clinic_id,
                Invoice.status == "paid",
                Invoice.issue_date >= date_from,
                Invoice.issue_date <= date_to,
                Invoice.deleted_at.is_(None),
            )
        )
        paid_count = result.scalar() or 0

        # Count overdue invoices. ``status in (issued, partial)`` implies
        # balance > 0 — fully paid invoices transition to ``paid``.
        today = date.today()
        result = await db.execute(
            select(func.count(Invoice.id)).where(
                Invoice.clinic_id == clinic_id,
                Invoice.status.in_(["issued", "partial"]),
                Invoice.due_date < today,
                Invoice.deleted_at.is_(None),
            )
        )
        overdue_count = result.scalar() or 0

        # Get VAT breakdown
        vat_breakdown = await BillingReportService._get_vat_breakdown(
            db, clinic_id, date_from, date_to
        )

        return {
            "period_start": date_from,
            "period_end": date_to,
            "total_invoiced": totals.total_invoiced,
            "total_paid": payments_totals.total_paid,
            "total_pending": total_pending,
            "invoice_count": totals.invoice_count,
            "paid_count": paid_count,
            "overdue_count": overdue_count,
            "vat_breakdown": vat_breakdown,
        }

    @staticmethod
    async def _get_vat_breakdown(
        db: AsyncSession,
        clinic_id: UUID,
        date_from: date,
        date_to: date,
    ) -> list[dict[str, Any]]:
        """Get VAT breakdown for a period (internal helper)."""
        result = await db.execute(
            select(
                InvoiceItem.vat_type_id,
                InvoiceItem.vat_rate,
                func.coalesce(
                    func.sum(InvoiceItem.line_subtotal - InvoiceItem.line_discount),
                    Decimal("0"),
                ).label("base_amount"),
                func.coalesce(func.sum(InvoiceItem.line_tax), Decimal("0")).label("tax_amount"),
            )
            .join(Invoice, InvoiceItem.invoice_id == Invoice.id)
            .where(
                Invoice.clinic_id == clinic_id,
                Invoice.status.notin_(["draft", "voided"]),
                Invoice.issue_date >= date_from,
                Invoice.issue_date <= date_to,
                Invoice.deleted_at.is_(None),
            )
            .group_by(InvoiceItem.vat_type_id, InvoiceItem.vat_rate)
        )
        vat_rows = result.all()

        # Get VAT type names
        vat_type_ids = [r.vat_type_id for r in vat_rows if r.vat_type_id]
        vat_names: dict[UUID, str] = {}
        if vat_type_ids:
            result = await db.execute(select(VatType).where(VatType.id.in_(vat_type_ids)))
            for vt in result.scalars():
                vat_names[vt.id] = vt.names.get("es", f"IVA {vt.rate}%")

        return [
            {
                "vat_type_id": row.vat_type_id,
                "vat_rate": row.vat_rate,
                "vat_name": vat_names.get(row.vat_type_id, f"IVA {row.vat_rate}%"),
                "base_amount": row.base_amount,
                "tax_amount": row.tax_amount,
                "total_amount": row.base_amount + row.tax_amount,
            }
            for row in vat_rows
        ]

    @staticmethod
    async def get_overdue_invoices(
        db: AsyncSession,
        clinic_id: UUID,
    ) -> list[dict[str, Any]]:
        """Get list of overdue invoices."""
        today = date.today()

        result = await db.execute(
            select(Invoice)
            .where(
                Invoice.clinic_id == clinic_id,
                Invoice.status.in_(["issued", "partial"]),
                Invoice.due_date < today,
                Invoice.deleted_at.is_(None),
            )
            .options(joinedload(Invoice.patient))
            .order_by(Invoice.due_date)
        )

        invoices = result.scalars().all()

        invoice_ids = [i.id for i in invoices]
        paid_by_inv: dict[UUID, Decimal] = {}
        if invoice_ids:
            paid_rows = await db.execute(
                select(InvoicePayment.invoice_id, func.sum(InvoicePayment.amount))
                .where(InvoicePayment.invoice_id.in_(invoice_ids))
                .group_by(InvoicePayment.invoice_id)
            )
            paid_by_inv = {row[0]: row[1] or Decimal("0") for row in paid_rows.all()}

        return [
            {
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "patient_name": (
                    f"{inv.patient.last_name}, {inv.patient.first_name}" if inv.patient else "-"
                ),
                "issue_date": inv.issue_date,
                "due_date": inv.due_date,
                "days_overdue": (today - inv.due_date).days,
                "balance_due": inv.total - paid_by_inv.get(inv.id, Decimal("0")),
            }
            for inv in invoices
        ]

    @staticmethod
    async def get_by_payment_method(
        db: AsyncSession,
        clinic_id: UUID,
        date_from: date,
        date_to: date,
    ) -> list[dict[str, Any]]:
        """Get payments breakdown by payment method (invoice-imputed only).

        Reads ``InvoicePayment`` joined with the payments module's
        ``Payment.method``. Patient-level "all collected" is in the
        payments module's own reports.
        """
        from app.modules.payments.models import Payment as PaymentModel

        result = await db.execute(
            select(
                PaymentModel.method.label("payment_method"),
                func.count(InvoicePayment.id).label("payment_count"),
                func.coalesce(func.sum(InvoicePayment.amount), Decimal("0")).label("total_amount"),
            )
            .join(PaymentModel, PaymentModel.id == InvoicePayment.payment_id)
            .where(
                InvoicePayment.clinic_id == clinic_id,
                PaymentModel.payment_date >= date_from,
                PaymentModel.payment_date <= date_to,
            )
            .group_by(PaymentModel.method)
            .order_by(desc("total_amount"))
        )

        return [
            {
                "payment_method": row.payment_method,
                "total_amount": row.total_amount,
                "payment_count": row.payment_count,
            }
            for row in result.all()
        ]

    @staticmethod
    async def get_by_professional(
        db: AsyncSession,
        clinic_id: UUID,
        date_from: date,
        date_to: date,
    ) -> list[dict[str, Any]]:
        """Get billing breakdown by professional (creator)."""
        result = await db.execute(
            select(
                Invoice.created_by,
                func.count(Invoice.id).label("invoice_count"),
                func.coalesce(func.sum(Invoice.total), Decimal("0")).label("total_invoiced"),
            )
            .where(
                Invoice.clinic_id == clinic_id,
                Invoice.status.notin_(["draft", "voided"]),
                Invoice.issue_date >= date_from,
                Invoice.issue_date <= date_to,
                Invoice.deleted_at.is_(None),
            )
            .group_by(Invoice.created_by)
        )
        rows = result.all()

        # Get user names
        user_ids = [r.created_by for r in rows]
        user_names: dict[UUID, str] = {}
        if user_ids:
            result = await db.execute(select(User).where(User.id.in_(user_ids)))
            for user in result.scalars():
                user_names[user.id] = f"{user.first_name} {user.last_name}"

        return [
            {
                "professional_id": row.created_by,
                "professional_name": user_names.get(row.created_by, "-"),
                "total_invoiced": row.total_invoiced,
                "invoice_count": row.invoice_count,
            }
            for row in rows
        ]

    @staticmethod
    async def get_vat_summary(
        db: AsyncSession,
        clinic_id: UUID,
        date_from: date,
        date_to: date,
    ) -> list[dict[str, Any]]:
        """Get VAT summary for accounting."""
        result = await db.execute(
            select(
                InvoiceItem.vat_type_id,
                InvoiceItem.vat_rate,
                func.coalesce(
                    func.sum(InvoiceItem.line_subtotal - InvoiceItem.line_discount),
                    Decimal("0"),
                ).label("base_amount"),
                func.coalesce(func.sum(InvoiceItem.line_tax), Decimal("0")).label("tax_amount"),
            )
            .join(Invoice, InvoiceItem.invoice_id == Invoice.id)
            .where(
                Invoice.clinic_id == clinic_id,
                Invoice.status.notin_(["draft", "voided"]),
                Invoice.issue_date >= date_from,
                Invoice.issue_date <= date_to,
                Invoice.deleted_at.is_(None),
            )
            .group_by(InvoiceItem.vat_type_id, InvoiceItem.vat_rate)
            .order_by(InvoiceItem.vat_rate)
        )
        rows = result.all()

        # Get VAT type names
        vat_type_ids = [r.vat_type_id for r in rows if r.vat_type_id]
        vat_names: dict[UUID, str] = {}
        if vat_type_ids:
            result = await db.execute(select(VatType).where(VatType.id.in_(vat_type_ids)))
            for vt in result.scalars():
                vat_names[vt.id] = vt.names.get("es", f"IVA {vt.rate}%")

        return [
            {
                "vat_type_id": row.vat_type_id,
                "vat_rate": row.vat_rate,
                "vat_name": vat_names.get(row.vat_type_id, f"IVA {row.vat_rate}%"),
                "base_amount": row.base_amount,
                "tax_amount": row.tax_amount,
                "total_amount": row.base_amount + row.tax_amount,
            }
            for row in rows
        ]

    @staticmethod
    async def get_numbering_gaps(
        db: AsyncSession,
        clinic_id: UUID,
    ) -> list[dict[str, Any]]:
        """Find gaps in invoice numbering.

        Returns list of gaps by series and year.
        """
        # Get all series for the clinic
        result = await db.execute(
            select(InvoiceSeries).where(
                InvoiceSeries.clinic_id == clinic_id,
                InvoiceSeries.is_active.is_(True),
            )
        )
        series_list = result.scalars().all()

        gaps = []

        for series in series_list:
            # Get all sequential numbers for this series, grouped by year
            # Only include issued invoices (those with sequential_number assigned)
            result = await db.execute(
                select(
                    func.extract("year", Invoice.created_at).label("year"),
                    Invoice.sequential_number,
                )
                .where(
                    Invoice.clinic_id == clinic_id,
                    Invoice.series_id == series.id,
                    Invoice.sequential_number.isnot(None),  # Only issued invoices
                    Invoice.deleted_at.is_(None),
                )
                .order_by("year", Invoice.sequential_number)
            )
            rows = result.all()

            # Group by year
            by_year: dict[int, list[int]] = {}
            for row in rows:
                year = int(row.year)
                if year not in by_year:
                    by_year[year] = []
                by_year[year].append(row.sequential_number)

            # Find gaps in each year
            for year, numbers in by_year.items():
                if not numbers:
                    continue

                numbers = sorted(set(numbers))
                expected = set(range(1, max(numbers) + 1))
                found = set(numbers)
                missing = sorted(expected - found)

                if missing:
                    gaps.append(
                        {
                            "series_prefix": series.prefix,
                            "year": year,
                            "missing_numbers": missing,
                        }
                    )

        return gaps
