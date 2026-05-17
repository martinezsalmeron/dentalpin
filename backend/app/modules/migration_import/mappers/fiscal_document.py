"""Map ``fiscal_document`` → ``billing.Invoice`` (+ optional verifactu).

This mapper is the only place in the importer that has a **runtime**
dependency on another module (``verifactu``). Per the project's
internationalisation goal — same module must work for PT/FR clinics
where Verifactu doesn't apply — ``verifactu`` is intentionally absent
from ``manifest.depends``.

Behaviour matrix:

| verifactu loaded | operator opt-in | legal hashes |
|------------------|-----------------|--------------|
| no               | _ignored_       | dropped, ``verifactu.skipped`` warning |
| yes              | False           | dropped, ``verifactu.opt_out`` warning |
| yes              | True            | preserved verbatim (never re-signed)  |

The opt-in flag lives on :attr:`ImportJob.import_fiscal_compliance`,
set by the execute request body.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID, uuid4

from app.core.plugins import module_registry

from ..models import ImportWarning
from .base import MapperContext

logger = logging.getLogger(__name__)

# Field names per DPMF CanonicalFiscalDocument that we preserve when
# verifactu is loaded + opt-in is true.
_LEGAL_FIELDS = (
    "legal_hash",
    "hash",
    "hash_control",
    "atcud",
    "qr_code",
)


def _verifactu_active(ctx: MapperContext) -> bool:
    return ctx.import_fiscal_compliance and module_registry.is_loaded("verifactu")


class FiscalDocumentMapper:
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
        existing = await ctx.resolver.get("fiscal_document", canonical_uuid)
        if existing is not None:
            return existing

        # billing.InvoiceService is the right target, but its create
        # signature couples to budget/treatment_plan in a way that
        # doesn't fit a historical import (it expects unbilled items).
        # We persist the *legal* surface (number, series, totals, dates,
        # hashes) directly via the Invoice model so downstream reports
        # see the historical record without re-issuing.
        from app.modules.billing.models import Invoice

        invoice = Invoice(
            id=uuid4(),
            clinic_id=ctx.clinic_id,
            patient_id=await self._resolve_patient(ctx, payload, source_id),
            series=payload.get("series") or "MIG",
            number=payload.get("number") or source_id,
            issued_at=_parse_date(payload.get("issued_at")),
            status=_map_status(payload.get("status")),
            total=_decimal(payload.get("total"), default="0"),
            tax_total=_decimal(payload.get("tax_total"), default="0"),
            subtotal=_decimal(payload.get("subtotal"), default="0"),
        )

        if _verifactu_active(ctx):
            self._stamp_legal_fields(invoice, payload)
        else:
            await self._record_legal_skip(ctx, source_id, payload)

        ctx.db.add(invoice)
        await ctx.db.flush()

        await ctx.resolver.set(
            entity_type="fiscal_document",
            canonical_uuid=canonical_uuid,
            source_system=source_system,
            dentalpin_table="invoices",
            dentalpin_id=invoice.id,
        )
        return invoice.id

    @staticmethod
    async def _resolve_patient(ctx: MapperContext, payload: dict[str, Any], source_id: str) -> UUID:
        external = payload.get("patient_uuid")
        if not external:
            raise ValueError(f"fiscal_document {source_id} missing patient_uuid")
        patient_id = await ctx.resolver.get("patient", str(external))
        if patient_id is None:
            raise ValueError(f"fiscal_document {source_id}: patient {external} not yet mapped")
        return patient_id

    @staticmethod
    def _stamp_legal_fields(invoice: Any, payload: dict[str, Any]) -> None:
        """Copy whichever legal-hash fields exist on the Invoice model.

        We use ``setattr`` so the mapper survives schema drift on the
        billing side — if a field disappears, we just skip it. The
        verifactu module owns the canonical field names today; we
        write the DPMF values verbatim regardless.
        """
        for field in _LEGAL_FIELDS:
            value = payload.get(field)
            if value and hasattr(invoice, field):
                setattr(invoice, field, value)

    @staticmethod
    async def _record_legal_skip(
        ctx: MapperContext, source_id: str, payload: dict[str, Any]
    ) -> None:
        has_legal = any(payload.get(field) for field in _LEGAL_FIELDS)
        if not has_legal:
            return
        code = (
            "verifactu.opt_out" if module_registry.is_loaded("verifactu") else "verifactu.skipped"
        )
        ctx.db.add(
            ImportWarning(
                job_id=ctx.job_id,
                entity_type="fiscal_document",
                source_id=source_id,
                severity="info",
                code=code,
                message=(
                    "Datos legales Verifactu omitidos (módulo ausente o no solicitado). "
                    "El documento se ha creado como factura comercial sin hashes legales."
                ),
                raw_data={f: payload.get(f) for f in _LEGAL_FIELDS if payload.get(f)},
            )
        )


def _decimal(value: Any, *, default: str) -> Any:
    from decimal import Decimal, InvalidOperation

    try:
        return Decimal(str(value)) if value is not None else Decimal(default)
    except (InvalidOperation, TypeError):
        return Decimal(default)


def _parse_date(value: Any):
    if not value:
        return None
    from datetime import date

    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def _map_status(value: Any) -> str:
    s = str(value or "").lower()
    if s in {"issued", "sent", "paid", "cancelled", "draft"}:
        return s
    return "issued"
