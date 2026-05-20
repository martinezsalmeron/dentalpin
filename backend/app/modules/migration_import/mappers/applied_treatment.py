"""Map ``applied_treatment`` → :class:`treatment_plan.PlannedTreatmentItem`.

DPMF's ``applied_treatment`` row is the clinical event: a patient
underwent (or is scheduled to undergo) a specific catalog entry. In
DentalPin this requires three rows in cooperation:

1. **One ``TreatmentPlan`` per (patient, source budget)**. Gesdén
   organises clinical activity around budgets; piling 100+ items
   into a single per-patient plan makes the UI unreadable. The
   mapper resolves ``applied_treatment.budget_line_uuid`` → its
   ``BudgetItem.budget_id`` and creates a plan titled after the
   source budget number ("Migrado — PRES-2024-0007"). Applied
   treatments without a budget link land in a "Migrado — sin
   presupuesto" catch-all per patient.
2. **One ``odontogram.Treatment``** for the actual tooth treatment
   record. ``clinical_type`` is derived from the raw Gesdén
   ``IdTipoOdg`` code via ``_TIPO_ODG_TO_CLINICAL_TYPE`` so the UI
   shows real names ("filling_composite", "implant", "crown" …)
   instead of every row landing as the catch-all "migrated". The
   catalog item is also linked so the imported budget/treatment
   inherits the destination catalog's pricing strategy and labels.
3. **One ``PlannedTreatmentItem``** linking the plan and the
   treatment.

The ``applied_treatment_phase`` mapper attaches sessions to the
``PlannedTreatmentItem`` produced here.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from sqlalchemy import select

from app.modules.budget.models import Budget, BudgetItem
from app.modules.odontogram.models import ToothRecord, Treatment, TreatmentTooth
from app.modules.payments.models import PatientEarnedEntry
from app.modules.treatment_plan.models import PlannedTreatmentItem, TreatmentPlan

from ..models import ImportWarning
from .base import MapperContext

# Gesdén ``TtosMed.StaTto`` codes that mean "treatment was performed".
# 5 dominates (~99 % of finished work) and 6 is a low-volume variant
# also carrying ``FecFin``. The remaining codes (3 = in active plan
# but not yet done, 1/2/4/8 = legacy/unclear) all leave ``FecFin``
# null in the source and stay as ``pending`` items.
_REALISED_CODES: set[int] = {5, 6}

# Threshold for the "notes longer than catalog name → likely
# performed" heuristic. Field validation against ``SOURCE_DB`` shows
# StaTto=3 averages 25 chars of notes (essentially just the catalog
# entry name), while StaTto=5 averages 91 chars (catalog name +
# clinical detail: implant lot, surfaces, dose, etc.). 40 chars sits
# above the noise floor and still catches the bulk of legitimately
# performed entries the clinic forgot to flag.
_NOTES_LIKELY_PERFORMED_MIN_CHARS = 40

# Heuristic age thresholds applied to ``FecIni`` for the
# "data-hygiene rescue" pass on StaTto=3 entries:
# - older than ``_OLD_TREATMENT_AGE_DAYS`` (5 years) → assume done
#   regardless of notes. A treatment planned but never done that long
#   ago is statistically negligible.
# - older than ``_MID_TREATMENT_AGE_DAYS`` (2 years) AND with notes
#   that exceed the catalog-name floor → assume done. The notes
#   length acts as the second corroborating signal.
_OLD_TREATMENT_AGE_DAYS = 365 * 5
_MID_TREATMENT_AGE_DAYS = 365 * 2

# Plan status to write for every migrated plan. Gesdén plans are by
# definition already-accepted historical records — leaving them in
# ``draft`` would force the operator to confirm each one manually
# before any consumer (budget, payments, reports) treats them as
# real. ``active`` is the post-acceptance state in DentalPin's plan
# machine and is the right migration target.
_MIGRATED_PLAN_STATUS = "active"

# Catch-all clinical_type for source rows whose ``IdTipoOdg`` doesn't
# map to a known DentalPin treatment vocabulary entry. Visible in
# warnings so the operator can backfill the mapping.
_FALLBACK_CLINICAL_TYPE = "migrated"

# Gesdén ``IdTipoOdg`` codes (from ``TTipoOdg``) → DentalPin
# ``TreatmentType`` enum values. Only odontogram-relevant codes are
# included; admin/audit codes (Anotación, Nota Económica, Visita No
# Atendida, Primera Visita, Nuevo Paciente, Bonos, Genérico, …) fall
# through to the catch-all because they aren't tooth treatments.
_TIPO_ODG_TO_CLINICAL_TYPE: dict[int, str] = {
    7: "band",  # Bandas
    8: "bracket",  # Brackets
    21: "root_canal_full",  # Endodoncia
    22: "filling_composite",  # Obturaciones
    23: "apicoectomy",  # Apicectomía
    24: "implant",  # Implante
    25: "post",  # Perno-Muñón
    26: "crown",  # Corona
    27: "bridge",  # Puente
    32: "sealant",  # Sellado
    33: "veneer",  # Carilla
    34: "filling_composite",  # Raspado → coarse fallback (no SRP enum yet)
    35: "extraction",  # Cirugía → most often extraction-related
    36: "extraction",  # Extracción Corona
    37: "extraction",  # Extracción Pieza
    44: "extraction",  # Rechazo Implante → records implant removal
    45: "extraction",  # Retirada Implante
    46: "implant",  # Reposición Implante
}

# Gesdén ``IdTipoOdg`` codes that aren't tooth-level clinical
# treatments — they're audit / non-clinical entries Gesdén lets the
# clinic park on the treatment timeline. Importing them as
# ``odontogram.Treatment`` rows pollutes the plan with line items
# that have no clinical meaning, so the mapper drops them on the
# floor (with an info warning + the canonical row still landing in
# ``RawEntity`` for audit).
_NON_CLINICAL_TIPO_ODG: set[int] = {
    1,  # Piezas Iniciales (tooth state)
    2,  # Posición Diente (orthodontic position state)
    3,  # Rotación Diente (orthodontic rotation state)
    4,  # Pieza Niño (deciduous presence)
    5,  # Pieza Adulto (permanent presence)
    6,  # SuperNumeraria (extra tooth)
    9,  # Nuevo Paciente
    10,  # Visita No Atendida
    11,  # Anotación
    12,  # Nota Económica
    13,  # Primera Visita
    14,  # Bonos
    38,  # Higiene (whole-mouth, not tooth-specific)
    39,  # Panorámicas (radiograph)
    40,  # Teleradio (radiograph)
    41,  # Fluorización (not tooth-specific)
    42,  # Genérico (meta)
}


class AppliedTreatmentMapper:
    def __init__(self) -> None:
        # (clinic_id, patient_id, budget_id_or_year) -> plan_id. One
        # plan per source budget keeps each plan to a manageable size;
        # the year slot is the per-patient catch-all for treatments
        # imported without a budget link, so 20 years of history fans
        # out into "Migrado — 2018", "Migrado — 2019", … rather than
        # one mega-plan.
        self._plan_cache: dict[tuple[UUID, UUID, UUID | int | None], UUID] = {}
        # plan_id -> next sequence_order to assign. Avoids a SELECT per item.
        self._next_sequence: dict[UUID, int] = {}
        # (clinic_id, patient_id, tooth_number) -> tooth_record_id. Lazy
        # creation of per-tooth state so TreatmentTooth has a valid FK
        # without us scanning the full odontogram up-front.
        self._tooth_cache: dict[tuple[UUID, UUID, int], UUID] = {}
        # budget_item_id -> budget_id. Resolved on first need; the
        # source can attach hundreds of applied_treatments to the same
        # budget so the cache pays for itself quickly.
        self._budget_for_item: dict[UUID, UUID] = {}

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
        existing = await ctx.resolver.get("applied_treatment", canonical_uuid)
        if existing is not None:
            return existing

        patient_uuid = payload.get("patient_uuid")
        if not patient_uuid:
            await _warn(ctx, source_id, "applied_treatment.no_patient", "Tratamiento omitido: sin paciente.")
            return None
        patient_id = await ctx.resolver.get("patient", str(patient_uuid))
        if patient_id is None:
            await _warn(
                ctx, source_id, "applied_treatment.unmapped_patient",
                "Tratamiento omitido: paciente no mapeado previamente.",
            )
            return None

        # Drop non-clinical Gesdén entries (notes, panoramic X-rays,
        # hygiene visits, generic memos…). They aren't tooth-level
        # treatments and importing them pollutes the destination plan
        # with empty line items. The canonical row still lands in
        # RawEntity via the catch-all so the audit trail isn't lost.
        id_tipo_odg = _coerce_int(raw.get("IdTipoOdg"))
        if id_tipo_odg in _NON_CLINICAL_TIPO_ODG:
            await _warn(
                ctx,
                source_id,
                "applied_treatment.non_clinical_entry",
                f"Entrada no clínica omitida (IdTipoOdg={id_tipo_odg}).",
            )
            return None

        professional_id: UUID | None = None
        prof_uuid = payload.get("professional_uuid")
        if prof_uuid:
            professional_id = await ctx.resolver.get("professional", str(prof_uuid))

        catalog_item_id: UUID | None = None
        variant_uuid = payload.get("treatment_variant_uuid")
        if variant_uuid:
            catalog_item_id = await ctx.resolver.get(
                "treatment_catalog_variant", str(variant_uuid)
            )

        # Resolve clinical_type from Gesdén's ``IdTipoOdg`` so the UI
        # surfaces real labels ("filling_composite", "implant", "crown"
        # …) instead of every row reading "migrated".
        clinical_type, was_resolved = _resolve_clinical_type(id_tipo_odg)
        if not was_resolved and id_tipo_odg not in (None, 0):
            await _warn(
                ctx,
                source_id,
                "applied_treatment.unmapped_tipo_odg",
                f"IdTipoOdg={id_tipo_odg} sin equivalente clínico en DentalPin; "
                f"se ha registrado como '{_FALLBACK_CLINICAL_TYPE}'.",
            )

        # Status & timestamps. ``StaTto`` 5/6 and ``FecFin`` presence
        # are the only formal Gesdén signals for "done", but this
        # specific export's data hygiene is poor — implants planned
        # 13 years ago that were obviously performed still sit at
        # StaTto=3 because the clinic never updated the flag. Apply
        # the corroborating heuristics decided in #ops:
        #
        #   1) StaTto ∈ {5, 6}                 → done (formal)
        #   2) FecFin set                       → done (formal)
        #   3) FecIni older than 5 years        → done (age alone)
        #   4) FecIni older than 2 years AND
        #      notes longer than the catalog
        #      name floor (40 chars)            → done (age + clinical detail)
        #
        # Every heuristic-triggered hit emits an audit warning so the
        # operator can spot-check the reclassification.
        status_code = _coerce_int(payload.get("status_code"))
        start_dt = _parse_datetime(payload.get("start_date")) or datetime.now(UTC)
        end_dt = _parse_datetime(payload.get("end_date"))
        amount = _decimal_or_none(payload.get("amount"))

        formal_done = status_code in _REALISED_CODES or end_dt is not None
        is_realised = formal_done
        if not is_realised:
            notes_value = payload.get("notes") or ""
            notes_chars = len(notes_value)
            age_days = (datetime.now(UTC) - start_dt).days
            if age_days >= _OLD_TREATMENT_AGE_DAYS:
                is_realised = True
                await _warn(
                    ctx,
                    source_id,
                    "applied_treatment.completed_by_age",
                    f"Tratamiento marcado como realizado por antigüedad "
                    f"({age_days // 365} años desde FecIni); Gesdén lo "
                    "deja en StaTto=3.",
                )
            elif (
                age_days >= _MID_TREATMENT_AGE_DAYS
                and notes_chars > _NOTES_LIKELY_PERFORMED_MIN_CHARS
            ):
                is_realised = True
                await _warn(
                    ctx,
                    source_id,
                    "applied_treatment.completed_by_notes",
                    f"Tratamiento marcado como realizado por notas "
                    f"clínicas ({notes_chars} chars) sobre tratamiento "
                    f"antiguo ({age_days // 365} años); StaTto=3 en "
                    "Gesdén.",
                )

        # When the heuristic says "done" but Gesdén has no end date,
        # use FecIni as an approximation so DentalPin's reports have
        # a date to anchor on.
        if is_realised and end_dt is None and not formal_done:
            end_dt = start_dt

        # Plan grouping: prefer the source budget link (one plan per
        # source presupuesto). When the source has no budget for this
        # treatment, fall back to a per-year bucket so a patient with
        # 20 years of history doesn't end up with one mega-plan.
        budget_id = await self._budget_for_applied_treatment(ctx, payload)
        year_for_grouping = (
            start_dt.year if budget_id is None and start_dt else None
        )
        plan_id = await self._get_or_create_plan(
            ctx, patient_id, budget_id, year=year_for_grouping
        )

        # 1) odontogram.Treatment header — clinical record.
        treatment = Treatment(
            clinic_id=ctx.clinic_id,
            patient_id=patient_id,
            clinical_type=clinical_type,
            scope="tooth",
            catalog_item_id=catalog_item_id,
            status="performed" if is_realised else "planned",
            recorded_at=start_dt,
            performed_at=end_dt if is_realised else None,
            performed_by=professional_id if is_realised else None,
            price_snapshot=amount,
            notes=payload.get("notes"),
            source_module="migration_import",
        )
        ctx.db.add(treatment)
        await ctx.db.flush()

        # 1b) TreatmentTooth children — populate from the decoded teeth
        # the dental-bridge transformer emits (PiezasAdu + PiezasLec
        # bit-mask decode). Surfaces remain ``None`` until the
        # ``ZonasPieza`` encoding is field-validated.
        teeth = payload.get("teeth") or []
        for tooth_number in teeth:
            tooth_record_id = await self._tooth_record_id(
                ctx, patient_id=patient_id, tooth_number=int(tooth_number)
            )
            ctx.db.add(
                TreatmentTooth(
                    treatment_id=treatment.id,
                    tooth_record_id=tooth_record_id,
                    tooth_number=int(tooth_number),
                )
            )
        if teeth:
            await ctx.db.flush()

        # 2) PlannedTreatmentItem — links the plan to the Treatment.
        sequence = self._next_sequence.get(plan_id, 0) + 1
        self._next_sequence[plan_id] = sequence
        item = PlannedTreatmentItem(
            clinic_id=ctx.clinic_id,
            treatment_plan_id=plan_id,
            treatment_id=treatment.id,
            sequence_order=sequence,
            status="completed" if is_realised else "pending",
            completed_at=end_dt if is_realised else None,
            completed_by=professional_id if is_realised else None,
            assigned_professional_id=professional_id,
            notes=payload.get("notes"),
        )
        ctx.db.add(item)
        await ctx.db.flush()

        # 3) PatientEarnedEntry — the patient ledger feeds off this
        # table. The normal flow populates it via
        # ``treatment_plan.item_session_completed`` /
        # ``odontogram.treatment.performed`` event handlers in
        # payments. Migration writes via the model directly to skip
        # the event chain (we don't want spurious notifications for
        # historic data) but we *must* still create the row, otherwise
        # completed treatments don't count against the payments
        # received and the balance reads "patient has a huge credit".
        #
        # **Only formal-done treatments count toward earnings.** The
        # heuristic above (age / notes) promotes ``is_realised`` so
        # the UI shows old planned treatments as completed, but
        # promoting them in the financial ledger would invent revenue
        # the clinic hasn't necessarily earned. Patients who paid
        # up-front for an implant plan typically have legitimate
        # credit until each piece is actually performed; counting the
        # whole plan as earned the moment we import would erase that
        # credit.
        if formal_done and amount is not None and amount > 0:
            ctx.db.add(
                PatientEarnedEntry(
                    clinic_id=ctx.clinic_id,
                    patient_id=patient_id,
                    treatment_id=treatment.id,
                    catalog_item_id=catalog_item_id,
                    amount=amount,
                    performed_at=end_dt or start_dt,
                    professional_id=professional_id,
                    source_event="migration_import",
                    description=(payload.get("notes") or "")[:160] or None,
                )
            )
            await ctx.db.flush()

        await ctx.resolver.set(
            entity_type="applied_treatment",
            canonical_uuid=canonical_uuid,
            source_system=source_system,
            dentalpin_table="planned_treatment_items",
            dentalpin_id=item.id,
        )
        return item.id

    async def _tooth_record_id(
        self, ctx: MapperContext, *, patient_id: UUID, tooth_number: int
    ) -> UUID:
        """Resolve (or lazily create) the ``ToothRecord`` for a patient/tooth pair.

        Re-runs are safe — an existing row is reused. New rows land
        with ``general_condition='healthy'`` and an empty ``surfaces``
        map; subsequent clinical activity in DentalPin overlays state
        on top.
        """
        key = (ctx.clinic_id, patient_id, tooth_number)
        if key in self._tooth_cache:
            return self._tooth_cache[key]

        result = await ctx.db.execute(
            select(ToothRecord.id).where(
                ToothRecord.clinic_id == ctx.clinic_id,
                ToothRecord.patient_id == patient_id,
                ToothRecord.tooth_number == tooth_number,
            )
        )
        tooth_id = result.scalar_one_or_none()
        if tooth_id is None:
            tooth_type = "permanent" if 11 <= tooth_number <= 48 else "deciduous"
            record = ToothRecord(
                clinic_id=ctx.clinic_id,
                patient_id=patient_id,
                tooth_number=tooth_number,
                tooth_type=tooth_type,
                general_condition="healthy",
                surfaces={},
            )
            ctx.db.add(record)
            await ctx.db.flush()
            tooth_id = record.id

        self._tooth_cache[key] = tooth_id
        return tooth_id

    async def _budget_for_applied_treatment(
        self, ctx: MapperContext, payload: dict[str, Any]
    ) -> UUID | None:
        """Walk ``applied_treatment.budget_line_uuid`` → its budget."""
        budget_line_uuid = payload.get("budget_line_uuid")
        if not budget_line_uuid:
            return None
        budget_item_id = await ctx.resolver.get("budget_line", str(budget_line_uuid))
        if budget_item_id is None:
            return None
        if budget_item_id in self._budget_for_item:
            return self._budget_for_item[budget_item_id]
        result = await ctx.db.execute(
            select(BudgetItem.budget_id).where(BudgetItem.id == budget_item_id)
        )
        budget_id = result.scalar_one_or_none()
        if budget_id is not None:
            self._budget_for_item[budget_item_id] = budget_id
        return budget_id

    async def _get_or_create_plan(
        self,
        ctx: MapperContext,
        patient_id: UUID,
        budget_id: UUID | None,
        year: int | None = None,
    ) -> UUID:
        cache_key = (ctx.clinic_id, patient_id, budget_id if budget_id else year)
        if cache_key in self._plan_cache:
            return self._plan_cache[cache_key]

        # Per-budget plan title carries the source budget number for
        # human navigation; the per-year fallback keeps catch-all
        # plans tractable when the source carries no budget link.
        if budget_id is not None:
            result = await ctx.db.execute(
                select(Budget.budget_number).where(Budget.id == budget_id)
            )
            budget_number = result.scalar_one_or_none() or str(budget_id)[:8]
            title = f"Migrado — {budget_number}"
            plan_number = f"MIG-{budget_number}"
            notes = (
                f"Plan generado por dental-bridge para tratamientos del "
                f"presupuesto {budget_number}."
            )
        elif year is not None:
            title = f"Migrado — {year}"
            plan_number = f"MIG-{str(patient_id)[:8]}-{year}"
            notes = (
                f"Plan generado por dental-bridge para tratamientos "
                f"realizados en {year} sin presupuesto de origen."
            )
        else:
            title = "Migrado — sin fecha"
            plan_number = f"MIG-{str(patient_id)[:8]}-ND"
            notes = (
                "Plan generado por dental-bridge para tratamientos sin "
                "presupuesto ni fecha de origen."
            )

        # Idempotent lookup so re-imports don't multiply plans.
        result = await ctx.db.execute(
            select(TreatmentPlan.id).where(
                TreatmentPlan.clinic_id == ctx.clinic_id,
                TreatmentPlan.patient_id == patient_id,
                TreatmentPlan.plan_number == plan_number,
            )
        )
        plan_id = result.scalar_one_or_none()
        if plan_id is None:
            # Bypass ``TreatmentPlanService.create`` — its
            # ``count(*)``-based plan-number generator collides after
            # any historic delete leaves gaps, and re-importing under
            # gap conditions throws ``uq_treatment_plan_number``. The
            # synthetic ``MIG-<budget_number>`` / ``MIG-<patient>-NB``
            # is deterministic, unique per (clinic, patient,
            # budget_or_none) and immediately re-runnable.
            plan = TreatmentPlan(
                clinic_id=ctx.clinic_id,
                patient_id=patient_id,
                plan_number=plan_number,
                title=title,
                status=_MIGRATED_PLAN_STATUS,
                internal_notes=notes,
                budget_id=budget_id,
                created_by=ctx.created_by,
            )
            ctx.db.add(plan)
            await ctx.db.flush()
            plan_id = plan.id

        self._plan_cache[cache_key] = plan_id
        return plan_id


def _coerce_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _resolve_clinical_type(id_tipo_odg: int | None) -> tuple[str, bool]:
    """Return ``(clinical_type, was_resolved)`` for a Gesdén ``IdTipoOdg``."""
    if id_tipo_odg is None:
        return _FALLBACK_CLINICAL_TYPE, False
    mapped = _TIPO_ODG_TO_CLINICAL_TYPE.get(id_tipo_odg)
    if mapped is None:
        return _FALLBACK_CLINICAL_TYPE, False
    return mapped, True


async def _warn(ctx: MapperContext, source_id: str, code: str, message: str) -> None:
    ctx.db.add(
        ImportWarning(
            job_id=ctx.job_id,
            entity_type="applied_treatment",
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


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=UTC)
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
    except (TypeError, ValueError):
        try:
            d = date.fromisoformat(str(value)[:10])
            return datetime(d.year, d.month, d.day, tzinfo=UTC)
        except (TypeError, ValueError):
            return None
