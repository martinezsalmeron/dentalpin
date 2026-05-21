"""Map ``budget_line`` → :class:`budget.BudgetItem`.

This mapper bypasses :class:`BudgetItemService.create_item` and writes
the model directly because the service path is too heavy for bulk
migration:

- ``BudgetItemService.create_item`` does ``db.get(TreatmentCatalogItem)``
  + ``db.get(VatType)`` + ``db.refresh(item, [...])`` after the insert,
  giving four extra round-trips per row. We already validated the
  catalog item via the resolver, so the lookup is redundant; we cache
  the VAT info per catalog_item_id; and the post-insert refresh is for
  the HTTP response, which the migration doesn't need.
- The original code also called ``db.get(Budget, budget_id)`` plus
  ``BudgetService._recalculate_totals`` per line — O(N²) per budget. The
  recalc is deferred to ``service._finalise_migrated_budgets``; the
  status promotion is hoisted into the post-pipeline pass too (we just
  collect the budget_ids that saw at least one ``applied_treatment_uuid``
  on this run).

Each line still needs:

- ``budget_id`` via the resolver against the already-mapped ``budget``.
- ``catalog_item_id`` via the resolver against ``treatment_catalog_item``
  (canonical ``treatment_uuid``) — falls back to the variant when the
  source only ships a per-tariff variant_uuid.

Pricing fields (``unit_amount``, ``units``, ``discount_*``,
``vat_percent``) carry over verbatim and we compute the line totals
inline with the same formula as ``BudgetItemService._calculate_line_totals``.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select

from app.modules.budget.models import BudgetItem
from app.modules.catalog.models import TreatmentCatalogItem, VatType

from ..models import ImportWarning
from .base import MapperContext


class BudgetLineMapper:
    def __init__(self) -> None:
        # catalog_item_id -> (vat_type_id, vat_rate). First lookup loads
        # from DB; subsequent lines reusing the same catalog item read
        # from this dict. 200 catalog items × 385K lines ⇒ 99.95% hit.
        self._vat_cache: dict[UUID, tuple[UUID | None, float]] = {}
        # Budgets that have already had at least one line marked as
        # "accepted" — applied once per budget at the post-pipeline pass
        # by ``service._finalise_migrated_budgets`` to avoid one UPDATE
        # per line.
        self._budgets_to_accept: set[UUID] = set()
        # (budget_item_id, applied_treatment_uuid) pairs collected while
        # iterating budget_lines. The applied_treatment mapper hasn't
        # run yet (it's level 4 in the entity order), so we can't
        # resolve to a Treatment.id here. The post-pipeline pass
        # ``service._finalise_migrated_budgets`` walks this list and
        # back-fills ``BudgetItem.treatment_id`` ↔ ``Treatment.budget_item_id``
        # once the applied_treatment mappings exist. The reverse-link
        # path on the applied_treatment mapper (``budget_line_uuid`` →
        # BudgetItem) only fires for the 0.9% of treatments whose
        # source row carries the back-ref — Gesdén populates the
        # forward link (this list) for 95% of rows.
        self._pending_treatment_links: list[tuple[UUID, str]] = []

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
        existing = await ctx.resolver.get("budget_line", canonical_uuid)
        if existing is not None:
            return existing

        budget_uuid = payload.get("budget_uuid")
        if not budget_uuid:
            await _warn(ctx, source_id, "budget_line.no_budget", "Línea sin presupuesto.")
            return None
        budget_id = await ctx.resolver.get("budget", str(budget_uuid))
        if budget_id is None:
            await _warn(
                ctx,
                source_id,
                "budget_line.unmapped_budget",
                "Línea omitida: presupuesto padre no mapeado.",
            )
            return None

        # Prefer the parent treatment; fall back to the variant if the
        # source only carries a per-tariff variant_uuid. Both resolve to
        # the same TreatmentCatalogItem.
        catalog_item_id = None
        if payload.get("treatment_uuid"):
            catalog_item_id = await ctx.resolver.get(
                "treatment_catalog_item", str(payload["treatment_uuid"])
            )
        if catalog_item_id is None and payload.get("treatment_variant_uuid"):
            catalog_item_id = await ctx.resolver.get(
                "treatment_catalog_variant", str(payload["treatment_variant_uuid"])
            )
        if catalog_item_id is None:
            code = (
                "budget_line.no_treatment"
                if not (payload.get("treatment_uuid") or payload.get("treatment_variant_uuid"))
                else "budget_line.unmapped_treatment"
            )
            msg = (
                "Línea omitida: sin tratamiento de catálogo en origen."
                if code == "budget_line.no_treatment"
                else "Línea omitida: tratamiento/variante de catálogo no mapeado."
            )
            await _warn(ctx, source_id, code, msg)
            return None

        unit_price = _decimal_or_none(payload.get("unit_amount")) or Decimal("0.00")
        units = payload.get("units")
        try:
            quantity = int(Decimal(str(units))) if units else 1
        except (InvalidOperation, TypeError, ValueError):
            quantity = 1
        quantity = max(quantity, 1)

        discount_percent = _decimal_or_none(payload.get("discount_percent"))
        discount_amount = _decimal_or_none(payload.get("discount_amount"))
        if discount_amount and discount_amount > 0:
            discount_type: str | None = "absolute"
            discount_value: Decimal | None = discount_amount
        elif discount_percent and discount_percent > 0:
            discount_type = "percentage"
            discount_value = discount_percent
        else:
            discount_type = None
            discount_value = None

        # DPMF lines may resolve to several teeth (e.g. bridges). DentalPin's
        # BudgetItem.tooth_number is scalar, so we record the first decoded
        # FDI here and surface the full list in ``notes`` so the operator
        # can split the line afterwards if needed.
        teeth = payload.get("teeth") or []
        tooth_number = int(teeth[0]) if teeth else None
        extra_teeth_note = (
            f"Dientes adicionales en origen: {', '.join(str(t) for t in teeth[1:])}."
            if len(teeth) > 1
            else None
        )
        base_notes = payload.get("notes")
        combined_notes = "\n".join(n for n in (base_notes, extra_teeth_note) if n) or None

        vat_type_id, vat_rate = await self._vat_info(ctx, catalog_item_id)

        # Compute line totals inline (mirrors
        # ``BudgetItemService._calculate_line_totals`` so a manual recalc
        # post-import sees the same numbers).
        line_subtotal = (unit_price * Decimal(quantity)).quantize(Decimal("0.01"))
        line_discount = Decimal("0.00")
        if discount_value is not None and discount_type:
            if discount_type == "percentage":
                line_discount = (line_subtotal * discount_value / Decimal(100)).quantize(
                    Decimal("0.01")
                )
            else:
                line_discount = min(discount_value, line_subtotal).quantize(Decimal("0.01"))
        taxable = line_subtotal - line_discount
        line_tax = (taxable * Decimal(str(vat_rate)) / Decimal(100)).quantize(Decimal("0.01"))
        line_total = (taxable + line_tax).quantize(Decimal("0.01"))

        item = BudgetItem(
            id=uuid4(),
            clinic_id=ctx.clinic_id,
            budget_id=budget_id,
            catalog_item_id=catalog_item_id,
            unit_price=unit_price,
            quantity=quantity,
            discount_type=discount_type,
            discount_value=discount_value,
            vat_type_id=vat_type_id,
            vat_rate=vat_rate,
            tooth_number=tooth_number,
            display_order=payload.get("order_within_budget") or 0,
            notes=combined_notes,
            line_subtotal=line_subtotal,
            line_discount=line_discount,
            line_tax=line_tax,
            line_total=line_total,
        )
        ctx.db.add(item)
        await ctx.db.flush()

        # Status promotion: mark the budget for acceptance at the
        # post-pipeline pass (one UPDATE per budget instead of one per
        # line). The mapper instance survives across the whole job so
        # the set accumulates as we iterate budget_lines.
        applied_uuid = payload.get("applied_treatment_uuid")
        if applied_uuid not in (None, "") and budget_id not in self._budgets_to_accept:
            self._budgets_to_accept.add(budget_id)
        # Record the forward link so the post-pipeline pass can wire
        # BudgetItem.treatment_id once the applied_treatment mapper
        # has landed its Treatment row. Even when the budget is still
        # 'draft' (no acceptance) we keep the link — the source may
        # have created a TtosMed without flagging the budget; the
        # operator can interpret the link as "this line covers this
        # treatment" independently of acceptance.
        if applied_uuid not in (None, ""):
            self._pending_treatment_links.append((item.id, str(applied_uuid)))

        await ctx.resolver.set(
            entity_type="budget_line",
            canonical_uuid=canonical_uuid,
            source_system=source_system,
            dentalpin_table="budget_items",
            dentalpin_id=item.id,
        )
        return item.id

    async def _vat_info(
        self, ctx: MapperContext, catalog_item_id: UUID
    ) -> tuple[UUID | None, float]:
        cached = self._vat_cache.get(catalog_item_id)
        if cached is not None:
            return cached
        result = await ctx.db.execute(
            select(TreatmentCatalogItem.vat_type_id).where(
                TreatmentCatalogItem.id == catalog_item_id
            )
        )
        vat_type_id = result.scalar_one_or_none()
        vat_rate = 0.0
        if vat_type_id is not None:
            row = await ctx.db.execute(
                select(VatType.rate).where(VatType.id == vat_type_id)
            )
            vat_rate = float(row.scalar_one_or_none() or 0.0)
        info = (vat_type_id, vat_rate)
        self._vat_cache[catalog_item_id] = info
        return info


async def _warn(ctx: MapperContext, source_id: str, code: str, message: str) -> None:
    ctx.db.add(
        ImportWarning(
            job_id=ctx.job_id,
            entity_type="budget_line",
            source_id=source_id,
            severity="warn",
            code=code,
            message=message,
        )
    )


def _decimal_or_none(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
