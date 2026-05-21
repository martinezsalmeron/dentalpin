"""Map ``payment`` → :class:`payments.Payment`.

A DPMF Payment is a historical money-received record. It points at a
patient via the DPMF's `patient_uuid` (resolved through the mapping
table) and optionally carries `method` + `amount` + `paid_at`.

The DPMF debt / debt_payment_application graph is significantly richer
than DentalPin's flat Payment model — allocations land in `RawEntity`
today via the catch-all path. This MVP creates the Payment row only,
which is enough to keep the patient ledger balanced for the historical
data.
"""

from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from sqlalchemy import func, select

from app.modules.payments.models import PatientEarnedEntry

from ..models import ImportWarning
from .base import MapperContext

_METHOD_MAP: dict[str, str] = {
    "cash": "cash",
    "card": "card",
    "bank_transfer": "bank_transfer",
    "transfer": "bank_transfer",
    "direct_debit": "direct_debit",
    "insurance": "insurance",
    "mutua": "insurance",
    "other": "other",
}

# Gesdén ``DCobros.Tipo`` numeric code → DentalPin payment method
# enum. Based on the dominant values in the source database (Tipo=1 is
# the by-far most common, payment is cash/in-clinic; the others map to
# typical Spanish clinic patterns). Unknown codes fall back to
# "other" so the row still imports cleanly.
_PAYMENT_KIND_MAP: dict[int, str] = {
    1: "cash",
    2: "bank_transfer",
    3: "card",
    4: "direct_debit",
    5: "insurance",
}


class PaymentMapper:
    def __init__(self) -> None:
        # Clinic.currency is a snapshot field on payments.Payment;
        # resolved once per clinic and reused for the whole job.
        self._currency_cache: dict[UUID, str] = {}

    async def apply(
        self,
        ctx: MapperContext,
        *,
        entity_type: str,
        payload: dict[str, Any],
        raw: dict[str, Any],
        canonical_uuid: str,
        source_id: str,
        source_system: str,
    ) -> UUID | None:
        existing = await ctx.resolver.get("payment", canonical_uuid)
        if existing is not None:
            return existing

        # DPMF payments reference a Client (payer), not a Patient. Gesdén's
        # ``PacCli`` is M:N — one client (typically the head of household)
        # routinely pays for several patients (spouse + kids + dependants).
        # ``PatientClientLinkMapper`` records every (client, patient) pair
        # in ``ctx.client_to_patients``; we resolve the FULL list here so
        # a single ``PagoCli`` can be split proportionally across every
        # linked patient rather than dumped onto the first one mapped,
        # which used to inflate that patient's apparent credit while
        # leaving the rest of the family in apparent debt.
        client_uuid_external = payload.get("client_uuid")
        all_patient_ids: list[UUID] = []
        if client_uuid_external:
            all_patient_ids = list(ctx.client_to_patients.get(str(client_uuid_external), []))
        if not all_patient_ids:
            # Legacy single-patient fallback: try the sidecar (older
            # imports), then a direct ``patient_uuid`` from the payload.
            fallback: UUID | None = None
            if client_uuid_external:
                fallback = await ctx.resolver.get("patient_for_client", str(client_uuid_external))
            if fallback is None:
                patient_uuid_external = payload.get("patient_uuid")
                if patient_uuid_external:
                    fallback = await ctx.resolver.get("patient", str(patient_uuid_external))
            if fallback is None:
                await _warn(
                    ctx,
                    source_id,
                    "payment.no_patient_for_client",
                    "Pago omitido: cliente/paciente no resoluble (sin link o link no importado).",
                )
                return None
            all_patient_ids = [fallback]

        try:
            amount = Decimal(str(payload.get("amount") or "0"))
        except (InvalidOperation, TypeError):
            await _warn(ctx, source_id, "payment.invalid_amount", "Pago omitido: importe inválido.")
            return None
        if amount <= 0:
            await _warn(
                ctx, source_id, "payment.zero_amount", "Pago omitido: importe nulo o negativo."
            )
            return None

        # Canonical Payment exposes ``payment_kind`` (the source numeric
        # ``Tipo`` code) and ``payment_method_uuid`` (FK to the source
        # catalog). We only decode the numeric kind here — the catalog
        # path requires a payment_method catalog importer that doesn't
        # exist yet. Unknown kinds fall back to "other".
        method = _PAYMENT_KIND_MAP.get(payload.get("payment_kind"), "other")

        paid_at = _parse_date(
            payload.get("paid_on") or payload.get("paid_at") or payload.get("payment_date")
        )
        if paid_at is None:
            # Payment.payment_date is NOT NULL — fall back to today for
            # rows whose source date is missing/unparseable. The notes
            # field captures the migration provenance for audit.
            paid_at = date.today()

        currency = await self._currency_for_clinic(ctx)

        # Preserve original Gesdén cashier when available — falls back
        # to the migration admin when the source had no user link or
        # the referenced user wasn't imported.
        recorded_by = await ctx.resolver.resolve_actor(
            payload.get("user_uuid"), ctx.created_by
        )

        from app.modules.payments.models import Payment

        # Split across linked patients when the client covers more than
        # one. Weight by the earned ledger so a family member with more
        # work done absorbs proportionally more of the payment; if no
        # patient has any earned activity yet (paid-up-front cohort)
        # the split is even.
        shares = await self._split_amounts(ctx, amount, all_patient_ids)

        first_payment_id: UUID | None = None
        for idx, (pid, share_amount) in enumerate(shares):
            note_prefix = payload.get("notes") or f"Importado dental-bridge ({source_id})"
            if len(shares) > 1:
                note = (
                    f"{note_prefix} · reparto familiar {idx + 1}/{len(shares)} "
                    f"(cliente {client_uuid_external})"
                )
            else:
                note = note_prefix
            payment = Payment(
                clinic_id=ctx.clinic_id,
                patient_id=pid,
                amount=share_amount,
                currency=currency,
                method=method,
                payment_date=paid_at,
                notes=note,
                recorded_by=recorded_by,
            )
            ctx.db.add(payment)
            await ctx.db.flush()
            if first_payment_id is None:
                first_payment_id = payment.id

        if len(shares) > 1:
            await _warn(
                ctx,
                source_id,
                "payment.split_across_family",
                f"Pago {amount} repartido entre {len(shares)} pacientes del cliente "
                f"{client_uuid_external} (proporcional al ledger earned).",
            )

        # Resolver maps the canonical_uuid to the first split row; the
        # remaining shares stay unmapped (re-runs short-circuit at the
        # top of apply() so we don't duplicate).
        assert first_payment_id is not None
        await ctx.resolver.set(
            entity_type="payment",
            canonical_uuid=canonical_uuid,
            source_system=source_system,
            dentalpin_table="payments",
            dentalpin_id=first_payment_id,
        )
        return first_payment_id

    async def _split_amounts(
        self,
        ctx: MapperContext,
        total: Decimal,
        patient_ids: list[UUID],
    ) -> list[tuple[UUID, Decimal]]:
        """Distribute ``total`` across ``patient_ids`` weighted by each
        patient's existing ``PatientEarnedEntry`` sum, falling back to
        an even split when nobody has any earned activity yet.

        Rounding goes to two decimals; the last share absorbs any
        remainder so the splits sum exactly to ``total``.
        """
        n = len(patient_ids)
        if n == 1:
            return [(patient_ids[0], total)]
        # Pull earned-per-patient in one round-trip.
        rows = await ctx.db.execute(
            select(
                PatientEarnedEntry.patient_id,
                func.coalesce(func.sum(PatientEarnedEntry.amount), Decimal("0")),
            )
            .where(PatientEarnedEntry.patient_id.in_(patient_ids))
            .group_by(PatientEarnedEntry.patient_id)
        )
        earned_map: dict[UUID, Decimal] = {pid: Decimal("0") for pid in patient_ids}
        for pid, earned in rows.all():
            earned_map[pid] = earned or Decimal("0")
        weight_total = sum(earned_map.values())
        shares: list[tuple[UUID, Decimal]] = []
        if weight_total <= 0:
            # Even split.
            per = (total / Decimal(n)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            allocated = Decimal("0")
            for idx, pid in enumerate(patient_ids):
                if idx == n - 1:
                    share = total - allocated
                else:
                    share = per
                    allocated += per
                shares.append((pid, share))
        else:
            allocated = Decimal("0")
            for idx, pid in enumerate(patient_ids):
                if idx == n - 1:
                    share = total - allocated
                else:
                    share = (total * earned_map[pid] / weight_total).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                    allocated += share
                shares.append((pid, share))
        return shares

    async def _currency_for_clinic(self, ctx: MapperContext) -> str:
        if ctx.clinic_id in self._currency_cache:
            return self._currency_cache[ctx.clinic_id]
        from app.core.auth.models import Clinic

        result = await ctx.db.execute(select(Clinic.currency).where(Clinic.id == ctx.clinic_id))
        currency = result.scalar_one_or_none() or "EUR"
        self._currency_cache[ctx.clinic_id] = currency
        return currency


async def _warn(ctx: MapperContext, source_id: str, code: str, message: str) -> None:
    ctx.db.add(
        ImportWarning(
            job_id=ctx.job_id,
            entity_type="payment",
            source_id=source_id,
            severity="warn",
            code=code,
            message=message,
        )
    )


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None
