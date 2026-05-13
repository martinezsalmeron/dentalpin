"""Read-side services for the payments module.

Write paths (create/refund/reallocate) live in ``workflow.py``. This
module hosts:
- ``PaymentService``      — list / get with eager loads
- ``PaymentReadService``  — narrow public surface other modules read
- ``LedgerService``       — patient ledger (KPIs + timeline)
- ``PaymentReportsService`` — clinic-wide reports
"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.core.auth.models import User

from .models import (
    PatientEarnedEntry,
    Payment,
    PaymentAllocation,
    Refund,
)
from .schemas import (
    AgingBucket,
    AgingBuckets,
    LedgerEntry,
    MethodBreakdown,
    PatientLedger,
    PaymentsSummary,
    PaymentsTrends,
    ProfessionalBreakdown,
    RefundsReport,
    TrendPoint,
)


class PaymentService:
    """List / get for ``Payment``."""

    @staticmethod
    async def list(
        db: AsyncSession,
        clinic_id: UUID,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
        method: str | None = None,
        patient_id: UUID | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Payment], int]:
        filters = [Payment.clinic_id == clinic_id]
        if date_from is not None:
            filters.append(Payment.payment_date >= date_from)
        if date_to is not None:
            filters.append(Payment.payment_date <= date_to)
        if method:
            filters.append(Payment.method == method)
        if patient_id:
            filters.append(Payment.patient_id == patient_id)

        total_result = await db.execute(select(func.count(Payment.id)).where(*filters))
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        query = (
            select(Payment)
            .where(*filters)
            .options(
                selectinload(Payment.allocations),
                selectinload(Payment.refunds),
                joinedload(Payment.recorder),
                joinedload(Payment.patient),
            )
            .order_by(desc(Payment.payment_date), desc(Payment.created_at))
            .offset(offset)
            .limit(page_size)
        )
        result = await db.execute(query)
        items = list(result.scalars().unique().all())
        return items, total

    @staticmethod
    async def get(db: AsyncSession, clinic_id: UUID, payment_id: UUID) -> Payment | None:
        result = await db.execute(
            select(Payment)
            .where(Payment.id == payment_id, Payment.clinic_id == clinic_id)
            .options(
                selectinload(Payment.allocations),
                selectinload(Payment.refunds),
                joinedload(Payment.recorder),
                joinedload(Payment.patient),
            )
        )
        return result.scalars().unique().one_or_none()


class PaymentReadService:
    """Narrow public surface other modules read.

    Billing reads from here to render "cobrado del presupuesto" on
    budget detail. Keep this surface minimal — additions need an ADR.
    """

    @staticmethod
    async def get_allocations_for_budget(
        db: AsyncSession, clinic_id: UUID, budget_id: UUID
    ) -> list[PaymentAllocation]:
        result = await db.execute(
            select(PaymentAllocation)
            .where(
                PaymentAllocation.clinic_id == clinic_id,
                PaymentAllocation.target_type == "budget",
                PaymentAllocation.budget_id == budget_id,
            )
            .options(joinedload(PaymentAllocation.payment))
            .order_by(PaymentAllocation.created_at)
        )
        return list(result.scalars().unique().all())

    @staticmethod
    async def total_collected_for_budget(
        db: AsyncSession, clinic_id: UUID, budget_id: UUID
    ) -> Decimal:
        result = await db.execute(
            select(func.coalesce(func.sum(PaymentAllocation.amount), Decimal("0"))).where(
                PaymentAllocation.clinic_id == clinic_id,
                PaymentAllocation.target_type == "budget",
                PaymentAllocation.budget_id == budget_id,
            )
        )
        return result.scalar_one()


# --- Ledger -----------------------------------------------------------


class LedgerService:
    """Patient-level KPIs + chronological timeline."""

    @staticmethod
    async def get_patient_ledger(
        db: AsyncSession, clinic_id: UUID, patient_id: UUID, currency: str
    ) -> PatientLedger:
        total_paid_row = await db.execute(
            select(
                func.coalesce(func.sum(Payment.amount), Decimal("0")),
            ).where(Payment.clinic_id == clinic_id, Payment.patient_id == patient_id)
        )
        total_paid: Decimal = total_paid_row.scalar_one()

        total_refunded_row = await db.execute(
            select(func.coalesce(func.sum(Refund.amount), Decimal("0")))
            .join(Payment, Payment.id == Refund.payment_id)
            .where(Payment.clinic_id == clinic_id, Payment.patient_id == patient_id)
        )
        total_refunded: Decimal = total_refunded_row.scalar_one()

        net_paid = total_paid - total_refunded

        total_earned_row = await db.execute(
            select(func.coalesce(func.sum(PatientEarnedEntry.amount), Decimal("0"))).where(
                PatientEarnedEntry.clinic_id == clinic_id,
                PatientEarnedEntry.patient_id == patient_id,
            )
        )
        total_earned: Decimal = total_earned_row.scalar_one()

        on_account_row = await db.execute(
            select(func.coalesce(func.sum(PaymentAllocation.amount), Decimal("0")))
            .join(Payment, Payment.id == PaymentAllocation.payment_id)
            .where(
                Payment.clinic_id == clinic_id,
                Payment.patient_id == patient_id,
                PaymentAllocation.target_type == "on_account",
            )
        )
        on_account_balance: Decimal = on_account_row.scalar_one()

        timeline = await LedgerService._build_timeline(db, clinic_id, patient_id)

        return PatientLedger(
            patient_id=patient_id,
            currency=currency,
            total_paid=net_paid,
            total_earned=total_earned,
            patient_credit=max(Decimal("0"), net_paid - total_earned),
            clinic_receivable=max(Decimal("0"), total_earned - net_paid),
            on_account_balance=on_account_balance,
            timeline=timeline,
        )

    @staticmethod
    async def _build_timeline(
        db: AsyncSession, clinic_id: UUID, patient_id: UUID
    ) -> list[LedgerEntry]:
        entries: list[LedgerEntry] = []

        # Payments
        result = await db.execute(
            select(Payment)
            .where(Payment.clinic_id == clinic_id, Payment.patient_id == patient_id)
            .order_by(Payment.payment_date)
        )
        for p in result.scalars().all():
            entries.append(
                LedgerEntry(
                    entry_type="payment",
                    occurred_at=datetime.combine(p.payment_date, datetime.min.time(), tzinfo=UTC),
                    amount=p.amount,
                    reference_id=p.id,
                    description=p.method,
                )
            )

        # Refunds
        result = await db.execute(
            select(Refund)
            .join(Payment, Payment.id == Refund.payment_id)
            .where(Payment.clinic_id == clinic_id, Payment.patient_id == patient_id)
        )
        for r in result.scalars().all():
            entries.append(
                LedgerEntry(
                    entry_type="refund",
                    occurred_at=r.refunded_at,
                    amount=-r.amount,
                    reference_id=r.id,
                    description=r.reason_code,
                )
            )

        # Earned
        result = await db.execute(
            select(PatientEarnedEntry).where(
                PatientEarnedEntry.clinic_id == clinic_id,
                PatientEarnedEntry.patient_id == patient_id,
            )
        )
        for e in result.scalars().all():
            entries.append(
                LedgerEntry(
                    entry_type="earned",
                    occurred_at=e.performed_at,
                    amount=e.amount,
                    reference_id=e.id,
                    description=e.source_event,
                )
            )

        entries.sort(key=lambda x: x.occurred_at)
        return entries


# --- Reports ----------------------------------------------------------


class PaymentReportsService:
    """Clinic-wide payment reports.

    Aggregations are paginated/bounded by the date range — never scan
    unbounded. Indexes ``idx_payments_clinic_date`` /
    ``idx_refund_clinic_date`` / ``idx_earned_clinic_performed``
    support the where-clauses.
    """

    @staticmethod
    async def summary(
        db: AsyncSession,
        clinic_id: UUID,
        currency: str,
        date_from: date,
        date_to: date,
    ) -> PaymentsSummary:
        # Collected (gross)
        result = await db.execute(
            select(
                func.coalesce(func.sum(Payment.amount), Decimal("0")),
                func.count(Payment.id),
            ).where(
                Payment.clinic_id == clinic_id,
                Payment.payment_date >= date_from,
                Payment.payment_date <= date_to,
            )
        )
        total_collected, payment_count = result.one()

        # Refunded
        result = await db.execute(
            select(
                func.coalesce(func.sum(Refund.amount), Decimal("0")),
                func.count(Refund.id),
            ).where(
                Refund.clinic_id == clinic_id,
                Refund.refunded_at >= datetime.combine(date_from, datetime.min.time(), tzinfo=UTC),
                Refund.refunded_at <= datetime.combine(date_to, datetime.max.time(), tzinfo=UTC),
            )
        )
        total_refunded, refund_count = result.one()

        # Patient credit / clinic receivable totals — sum across patients
        # who fall on each side of the (paid − earned) inequality.
        # Implemented in app code from per-patient aggregates.
        patient_credit_total, clinic_receivable_total = await PaymentReportsService._patient_totals(
            db, clinic_id
        )

        net = total_collected - total_refunded
        refund_ratio = float(total_refunded / total_collected) if total_collected else 0.0

        return PaymentsSummary(
            period_start=date_from,
            period_end=date_to,
            currency=currency,
            total_collected=total_collected,
            total_refunded=total_refunded,
            net_collected=net,
            patient_credit_total=patient_credit_total,
            clinic_receivable_total=clinic_receivable_total,
            refund_ratio=refund_ratio,
            payment_count=payment_count,
            refund_count=refund_count,
        )

    @staticmethod
    async def _patient_totals(db: AsyncSession, clinic_id: UUID) -> tuple[Decimal, Decimal]:
        """Sum per-patient credit and receivable across the clinic.

        Computed via Python aggregation over per-patient subtotals to
        avoid a heavier window query — clinic-scale row counts make this
        cheap and avoids SQL portability concerns.
        """
        paid_by_patient = await db.execute(
            select(Payment.patient_id, func.coalesce(func.sum(Payment.amount), Decimal("0")))
            .where(Payment.clinic_id == clinic_id)
            .group_by(Payment.patient_id)
        )
        paid = dict(paid_by_patient.all())

        refunded_by_patient = await db.execute(
            select(
                Payment.patient_id,
                func.coalesce(func.sum(Refund.amount), Decimal("0")),
            )
            .join(Refund, Refund.payment_id == Payment.id)
            .where(Payment.clinic_id == clinic_id)
            .group_by(Payment.patient_id)
        )
        refunded = dict(refunded_by_patient.all())

        earned_by_patient = await db.execute(
            select(
                PatientEarnedEntry.patient_id,
                func.coalesce(func.sum(PatientEarnedEntry.amount), Decimal("0")),
            )
            .where(PatientEarnedEntry.clinic_id == clinic_id)
            .group_by(PatientEarnedEntry.patient_id)
        )
        earned = dict(earned_by_patient.all())

        patient_credit = Decimal("0")
        clinic_receivable = Decimal("0")
        patient_ids = set(paid.keys()) | set(earned.keys())
        for pid in patient_ids:
            net_paid = paid.get(pid, Decimal("0")) - refunded.get(pid, Decimal("0"))
            net_earned = earned.get(pid, Decimal("0"))
            if net_paid > net_earned:
                patient_credit += net_paid - net_earned
            elif net_earned > net_paid:
                clinic_receivable += net_earned - net_paid

        return patient_credit, clinic_receivable

    @staticmethod
    async def by_method(
        db: AsyncSession,
        clinic_id: UUID,
        date_from: date,
        date_to: date,
    ) -> list[MethodBreakdown]:
        result = await db.execute(
            select(
                Payment.method,
                func.coalesce(func.sum(Payment.amount), Decimal("0")),
                func.count(Payment.id),
            )
            .where(
                Payment.clinic_id == clinic_id,
                Payment.payment_date >= date_from,
                Payment.payment_date <= date_to,
            )
            .group_by(Payment.method)
            .order_by(desc(func.sum(Payment.amount)))
        )
        return [MethodBreakdown(method=row[0], total=row[1], count=row[2]) for row in result.all()]

    @staticmethod
    async def by_professional(
        db: AsyncSession,
        clinic_id: UUID,
        date_from: date,
        date_to: date,
    ) -> list[ProfessionalBreakdown]:
        """Earned breakdown by professional (using earned ledger)."""
        result = await db.execute(
            select(
                PatientEarnedEntry.professional_id,
                func.coalesce(func.sum(PatientEarnedEntry.amount), Decimal("0")),
                func.count(PatientEarnedEntry.id),
            )
            .where(
                PatientEarnedEntry.clinic_id == clinic_id,
                PatientEarnedEntry.performed_at
                >= datetime.combine(date_from, datetime.min.time(), tzinfo=UTC),
                PatientEarnedEntry.performed_at
                <= datetime.combine(date_to, datetime.max.time(), tzinfo=UTC),
            )
            .group_by(PatientEarnedEntry.professional_id)
        )
        rows = list(result.all())
        prof_ids = [r[0] for r in rows if r[0] is not None]
        names: dict[UUID, str] = {}
        if prof_ids:
            users_result = await db.execute(select(User).where(User.id.in_(prof_ids)))
            for u in users_result.scalars():
                names[u.id] = f"{u.first_name} {u.last_name}".strip()
        return [
            ProfessionalBreakdown(
                professional_id=row[0],
                professional_name=names.get(row[0]) if row[0] else None,
                total_earned=row[1],
                count=row[2],
            )
            for row in rows
        ]

    @staticmethod
    async def aging_receivables(
        db: AsyncSession,
        clinic_id: UUID,
        currency: str,
    ) -> AgingBuckets:
        """Bucket clinic_receivable per patient by oldest unpaid earned entry.

        For each patient with ``earned > paid``, find the oldest
        ``PatientEarnedEntry`` and bucket by age. Receivable amount is
        ``earned − paid`` for that patient (positive only).
        """
        # Per-patient net paid (paid − refunded)
        paid_rows = await db.execute(
            select(
                Payment.patient_id,
                func.coalesce(func.sum(Payment.amount), Decimal("0")),
            )
            .where(Payment.clinic_id == clinic_id)
            .group_by(Payment.patient_id)
        )
        paid_per_patient = dict(paid_rows.all())

        refund_rows = await db.execute(
            select(
                Payment.patient_id,
                func.coalesce(func.sum(Refund.amount), Decimal("0")),
            )
            .join(Refund, Refund.payment_id == Payment.id)
            .where(Payment.clinic_id == clinic_id)
            .group_by(Payment.patient_id)
        )
        refunded_per_patient = dict(refund_rows.all())

        # Earned with oldest performed_at per patient
        earned_rows = await db.execute(
            select(
                PatientEarnedEntry.patient_id,
                func.coalesce(func.sum(PatientEarnedEntry.amount), Decimal("0")),
                func.min(PatientEarnedEntry.performed_at),
            )
            .where(PatientEarnedEntry.clinic_id == clinic_id)
            .group_by(PatientEarnedEntry.patient_id)
        )

        today = datetime.now(UTC).date()
        buckets_data: dict[str, dict[str, object]] = {
            "0-30": {"total": Decimal("0"), "patients": set()},
            "31-60": {"total": Decimal("0"), "patients": set()},
            "61-90": {"total": Decimal("0"), "patients": set()},
            "90+": {"total": Decimal("0"), "patients": set()},
        }

        for pid, earned_total, oldest_at in earned_rows.all():
            net_paid = paid_per_patient.get(pid, Decimal("0")) - refunded_per_patient.get(
                pid, Decimal("0")
            )
            receivable = earned_total - net_paid
            if receivable <= 0:
                continue

            age_days = (today - oldest_at.date()).days if oldest_at else 0
            if age_days <= 30:
                key = "0-30"
            elif age_days <= 60:
                key = "31-60"
            elif age_days <= 90:
                key = "61-90"
            else:
                key = "90+"

            buckets_data[key]["total"] = buckets_data[key]["total"] + receivable
            buckets_data[key]["patients"].add(pid)  # type: ignore[union-attr]

        return AgingBuckets(
            currency=currency,
            buckets=[
                AgingBucket(
                    label=label,
                    total=data["total"],  # type: ignore[arg-type]
                    patient_count=len(data["patients"]),  # type: ignore[arg-type]
                )
                for label, data in buckets_data.items()
            ],
        )

    @staticmethod
    async def refunds_report(
        db: AsyncSession,
        clinic_id: UUID,
        currency: str,
        date_from: date,
        date_to: date,
    ) -> RefundsReport:
        dt_from = datetime.combine(date_from, datetime.min.time(), tzinfo=UTC)
        dt_to = datetime.combine(date_to, datetime.max.time(), tzinfo=UTC)

        # By reason
        by_reason_rows = await db.execute(
            select(
                Refund.reason_code,
                func.coalesce(func.sum(Refund.amount), Decimal("0")),
                func.count(Refund.id),
            )
            .where(
                Refund.clinic_id == clinic_id,
                Refund.refunded_at >= dt_from,
                Refund.refunded_at <= dt_to,
            )
            .group_by(Refund.reason_code)
            .order_by(desc(func.sum(Refund.amount)))
        )
        by_reason = [
            {"reason_code": row[0], "total": row[1], "count": row[2]}
            for row in by_reason_rows.all()
        ]

        # By method
        by_method_rows = await db.execute(
            select(
                Refund.method,
                func.coalesce(func.sum(Refund.amount), Decimal("0")),
                func.count(Refund.id),
            )
            .where(
                Refund.clinic_id == clinic_id,
                Refund.refunded_at >= dt_from,
                Refund.refunded_at <= dt_to,
            )
            .group_by(Refund.method)
        )
        by_method = [
            MethodBreakdown(method=row[0], total=row[1], count=row[2])
            for row in by_method_rows.all()
        ]

        total_refunded = sum((r["total"] for r in by_reason), Decimal("0"))

        # Compare against gross collected in period for ratio
        collected_row = await db.execute(
            select(func.coalesce(func.sum(Payment.amount), Decimal("0"))).where(
                Payment.clinic_id == clinic_id,
                Payment.payment_date >= date_from,
                Payment.payment_date <= date_to,
            )
        )
        total_collected: Decimal = collected_row.scalar_one()
        refund_ratio = float(total_refunded / total_collected) if total_collected else 0.0

        return RefundsReport(
            period_start=date_from,
            period_end=date_to,
            currency=currency,
            total_refunded=total_refunded,
            refund_ratio=refund_ratio,
            by_reason=by_reason,
            by_method=by_method,
        )

    @staticmethod
    async def trends(
        db: AsyncSession,
        clinic_id: UUID,
        currency: str,
        date_from: date,
        date_to: date,
        granularity: str,
    ) -> PaymentsTrends:
        # Compute bucket starts in Python from raw rows; portable across
        # SQL dialects and avoids dialect-specific date_trunc usage.
        coll_rows = await db.execute(
            select(Payment.payment_date, Payment.amount).where(
                Payment.clinic_id == clinic_id,
                Payment.payment_date >= date_from,
                Payment.payment_date <= date_to,
            )
        )
        refunds_rows = await db.execute(
            select(Refund.refunded_at, Refund.amount).where(
                Refund.clinic_id == clinic_id,
                Refund.refunded_at >= datetime.combine(date_from, datetime.min.time(), tzinfo=UTC),
                Refund.refunded_at <= datetime.combine(date_to, datetime.max.time(), tzinfo=UTC),
            )
        )

        def bucket(d: date) -> date:
            if granularity == "day":
                return d
            if granularity == "week":
                return d - timedelta(days=d.weekday())
            if granularity == "month":
                return d.replace(day=1)
            if granularity == "year":
                return d.replace(month=1, day=1)
            return d

        agg: dict[date, dict[str, Decimal]] = defaultdict(
            lambda: {"collected": Decimal("0"), "refunded": Decimal("0")}
        )
        for dt, amount in coll_rows.all():
            agg[bucket(dt)]["collected"] += amount
        for refunded_at, amount in refunds_rows.all():
            agg[bucket(refunded_at.date())]["refunded"] += amount

        points = [
            TrendPoint(
                bucket_start=b,
                collected=v["collected"],
                refunded=v["refunded"],
                net=v["collected"] - v["refunded"],
            )
            for b, v in sorted(agg.items())
        ]

        return PaymentsTrends(
            granularity=granularity,  # type: ignore[arg-type]
            currency=currency,
            points=points,
        )
