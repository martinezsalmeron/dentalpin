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
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

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


class PaymentMapper:
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

        # Resolve patient — required FK.
        patient_uuid_external = payload.get("patient_uuid")
        if not patient_uuid_external:
            raise ValueError("payment missing patient_uuid")
        patient_id = await ctx.resolver.get("patient", str(patient_uuid_external))
        if patient_id is None:
            raise ValueError(f"payment {source_id}: patient {patient_uuid_external} not yet mapped")

        try:
            amount = Decimal(str(payload.get("amount") or "0"))
        except (InvalidOperation, TypeError) as exc:
            raise ValueError(f"payment {source_id}: invalid amount") from exc

        method = _METHOD_MAP.get((payload.get("method") or "").lower(), "other")

        paid_at_raw = payload.get("paid_at") or payload.get("payment_date")
        paid_at = None
        if paid_at_raw:
            try:
                paid_at = date.fromisoformat(paid_at_raw[:10])
            except (TypeError, ValueError):
                paid_at = None

        # Late import — payments service may not exist when migration_import
        # is loaded in isolation (e.g. uninstall test). Manifest depends on
        # payments so in production this is guaranteed available.
        from app.modules.payments.models import Payment

        payment = Payment(
            clinic_id=ctx.clinic_id,
            patient_id=patient_id,
            amount=amount,
            method=method,
            payment_date=paid_at,
            notes=payload.get("notes") or f"Importado dental-bridge ({source_id})",
            recorded_by=None,
        )
        ctx.db.add(payment)
        await ctx.db.flush()

        await ctx.resolver.set(
            entity_type="payment",
            canonical_uuid=canonical_uuid,
            source_system=source_system,
            dentalpin_table="payments",
            dentalpin_id=payment.id,
        )
        return payment.id
