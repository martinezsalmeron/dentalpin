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

from sqlalchemy import func, select

from app.modules.budget.models import Budget
from app.modules.budget.service import BudgetService

from ..models import ImportWarning
from .base import MapperContext


class BudgetMapper:
    def __init__(self) -> None:
        # year -> highest ``NNNN`` already in use for ``PRES-{year}-NNNN``
        # in the destination clinic. Seeded on first need from the
        # database, then bumped in-memory as each migrated budget lands.
        # Lets us hand out collision-free sequential numbers per year
        # without re-querying for every row.
        self._next_seq_per_year: dict[int, int] = {}

    async def _allocate_budget_number(
        self,
        ctx: MapperContext,
        payload: dict[str, Any],
        quote_date: date,
        source_id: str,
    ) -> str | None:
        return await _allocate_budget_number_impl(self, ctx, payload, quote_date, source_id)

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
            await _warn(
                ctx, source_id, "budget.no_patient", "Presupuesto omitido: sin paciente en origen."
            )
            return None
        patient_id = await ctx.resolver.get("patient", str(patient_uuid))
        if patient_id is None:
            await _warn(
                ctx,
                source_id,
                "budget.unmapped_patient",
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

        # Preserve historic chronology by keeping the source quote
        # year in the budget number ("PRES-2014-0027" instead of
        # renumbering decades-old presupuestos into 2026). We try the
        # source's own ``NumPre`` first so the migrated number matches
        # what the clinic saw in Gesdén; ``NumPre`` resets per patient
        # in Gesdén, so collisions are common and we fall through to
        # the next free slot in that same year (never the current
        # year, which is what ``BudgetService.generate_number`` would
        # have picked).
        proposed_number = await self._allocate_budget_number(ctx, payload, quote_date, source_id)

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
            "budget_number": proposed_number,
            "items": [],  # Lines added by budget_line mapper.
        }
        data = {k: v for k, v in data.items() if v is not None}

        # Preserve the original Gesdén author when available — falls
        # back to the migration admin when the source had no user link
        # or the referenced user wasn't imported.
        created_by = await ctx.resolver.resolve_actor(
            payload.get("elaborated_by_user_uuid"), ctx.created_by
        )
        budget = await BudgetService.create_budget(ctx.db, ctx.clinic_id, created_by, data)

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
        quote_dt = datetime(quote_date.year, quote_date.month, quote_date.day, tzinfo=UTC)
        budget.created_at = quote_dt
        latest = (
            _parse_date(payload.get("rejected_date"))
            or _parse_date(payload.get("accepted_date"))
            or quote_date
        )
        budget.updated_at = datetime(latest.year, latest.month, latest.day, tzinfo=UTC)

        await ctx.resolver.set(
            entity_type="budget",
            canonical_uuid=canonical_uuid,
            source_system=source_system,
            dentalpin_table="budgets",
            dentalpin_id=budget.id,
        )
        return budget.id


async def _allocate_budget_number_impl(
    mapper: BudgetMapper,
    ctx: MapperContext,
    payload: dict[str, Any],
    quote_date: date,
    source_id: str,
) -> str | None:
    """Pick the budget_number for one migrated row.

    Order of preference:
    1. ``PRES-{year}-{NumPre:04d}`` straight from the source when no
       row in the destination already holds it.
    2. ``PRES-{year}-{next_seq:04d}`` where ``next_seq`` is one past
       the highest in-clinic counter for that same year (warning
       emitted so the operator knows the source value was bumped).

    Returns ``None`` when nothing usable can be derived (no
    ``NumPre`` or no ``quote_date``); ``BudgetService.create_budget``
    then falls back to its current-year generator.
    """
    year = quote_date.year
    raw_number = payload.get("number")
    try:
        source_number = int(raw_number) if raw_number is not None else None
    except (TypeError, ValueError):
        source_number = None
    if source_number is not None and source_number > 0:
        candidate = f"PRES-{year}-{source_number:04d}"
        collision = await ctx.db.execute(
            select(Budget.id).where(
                Budget.clinic_id == ctx.clinic_id,
                Budget.budget_number == candidate,
            )
        )
        if collision.scalar_one_or_none() is None:
            # Keep our in-memory counter ahead of any source value we
            # have already accepted so the next collision picks a
            # number strictly greater than the highest used.
            if source_number > mapper._next_seq_per_year.get(year, 0):
                mapper._next_seq_per_year[year] = source_number
            return candidate
        await _warn(
            ctx,
            source_id,
            "budget.number_collision",
            f"NumPre={source_number} ya usado en {year}; se reasigna en la misma año.",
        )
    # Either no usable source number, or the source value collided.
    if year not in mapper._next_seq_per_year:
        mapper._next_seq_per_year[year] = await _max_seq_for_year(ctx, year)
    mapper._next_seq_per_year[year] += 1
    return f"PRES-{year}-{mapper._next_seq_per_year[year]:04d}"


_NUMBER_TAIL_RE = __import__("re").compile(r"-(\d+)$")


async def _max_seq_for_year(ctx: MapperContext, year: int) -> int:
    """Highest 4-digit tail already used as ``PRES-{year}-NNNN`` in the
    destination clinic (any version). Returns 0 when none exists."""
    result = await ctx.db.execute(
        select(func.max(Budget.budget_number)).where(
            Budget.clinic_id == ctx.clinic_id,
            Budget.budget_number.like(f"PRES-{year}-%"),
        )
    )
    existing = result.scalar_one_or_none()
    if not existing:
        return 0
    match = _NUMBER_TAIL_RE.search(existing)
    if not match:
        return 0
    try:
        return int(match.group(1))
    except ValueError:
        return 0


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
