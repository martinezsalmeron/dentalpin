"""Map ``budget`` → :class:`budget.Budget`.

Materialises the budget *header* via :func:`BudgetService.create_budget`
so the service-side number generation, validation and history audit
all fire identically to the interactive flow. Lines are handled by the
sibling ``budget_line`` mapper and FK back via the resolver.

Status derivation is best-effort: the canonical ``status_code`` is a
source-opaque integer, so we fall back to ``accepted_date`` /
``rejected_date`` presence to pick between ``draft``, ``accepted`` and
``rejected``.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

from app.modules.budget.service import BudgetService

from ..models import ImportWarning
from .base import MapperContext


class BudgetMapper:
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
        existing = await ctx.resolver.get("budget", canonical_uuid)
        if existing is not None:
            return existing

        patient_uuid = payload.get("patient_uuid")
        if not patient_uuid:
            await _warn(ctx, source_id, "budget.no_patient", "Presupuesto omitido: sin paciente en origen.")
            return None
        patient_id = await ctx.resolver.get("patient", str(patient_uuid))
        if patient_id is None:
            await _warn(
                ctx, source_id, "budget.unmapped_patient",
                "Presupuesto omitido: paciente no mapeado previamente.",
            )
            return None

        professional_id: UUID | None = None
        professional_uuid = payload.get("professional_uuid")
        if professional_uuid:
            professional_id = await ctx.resolver.get("professional", str(professional_uuid))

        quote_date = _parse_date(payload.get("quote_date")) or date.today()
        accepted = _parse_date(payload.get("accepted_date")) is not None
        rejected = _parse_date(payload.get("rejected_date")) is not None
        if rejected:
            status = "rejected"
        elif accepted:
            status = "accepted"
        else:
            status = "draft"

        title = payload.get("title")
        if title:
            title = str(title)[:200]
        patient_notes = payload.get("notes")

        data: dict[str, Any] = {
            "patient_id": patient_id,
            "status": status,
            "valid_from": quote_date,
            "assigned_professional_id": professional_id,
            "internal_notes": (
                f"Migrado dental-bridge — origen Gesdén {source_id}"
                + (f" · {title}" if title else "")
            ),
            "patient_notes": patient_notes,
            "items": [],  # Lines added by budget_line mapper.
        }
        data = {k: v for k, v in data.items() if v is not None}

        budget = await BudgetService.create_budget(
            ctx.db, ctx.clinic_id, ctx.created_by, data
        )

        if status != "draft":
            # Persist accepted/rejected metadata since create_budget
            # always starts in draft.
            budget.status = status
            if accepted:
                budget.accepted_via = "manual"
            if rejected:
                budget.rejection_reason = "other"
                budget.rejection_note = payload.get("rejection_observations")

        # Stamp the source's ``FecPresup`` as ``created_at`` so the UI
        # shows the real budget date instead of "today's import run".
        # ``TimestampMixin`` only seeds these columns from the
        # server-side ``func.now()`` default when the instance has no
        # value — overwriting after creation is safe and survives the
        # commit. ``updated_at`` follows the latest lifecycle event
        # (acceptance / rejection / quote).
        quote_dt = datetime(
            quote_date.year, quote_date.month, quote_date.day, tzinfo=UTC
        )
        budget.created_at = quote_dt
        latest = _parse_date(payload.get("rejected_date")) or _parse_date(
            payload.get("accepted_date")
        ) or quote_date
        budget.updated_at = datetime(latest.year, latest.month, latest.day, tzinfo=UTC)

        await ctx.resolver.set(
            entity_type="budget",
            canonical_uuid=canonical_uuid,
            source_system=source_system,
            dentalpin_table="budgets",
            dentalpin_id=budget.id,
        )
        return budget.id


async def _warn(ctx: MapperContext, source_id: str, code: str, message: str) -> None:
    ctx.db.add(
        ImportWarning(
            job_id=ctx.job_id,
            entity_type="budget",
            source_id=source_id,
            severity="warn",
            code=code,
            message=message,
        )
    )


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(UTC).date()
    except (TypeError, ValueError):
        try:
            return date.fromisoformat(str(value)[:10])
        except (TypeError, ValueError):
            return None
