"""Map ``treatment_catalog_item`` → :class:`catalog.TreatmentCatalogItem`.

DPMF carries treatment templates (the clinic's offer) as their own
entity. We materialise them in the destination catalog so budget and
treatment_plan mappers can FK-reference them via the resolver.

**Match-then-create**: before falling back to a new catalog row we
look for an existing ``TreatmentCatalogItem`` whose Spanish name
matches the source. Matching is accent/punctuation-insensitive and
falls back to a similarity score (``difflib`` ratio ≥ 0.88) when the
exact normalised form misses — Gesdén labels carry abbreviations and
dots ("OBTUR. COMP.", "ENDODONCIA UNI.") that would otherwise never
match the destination seed ("Obturación composite", "Endodoncia
unirradicular"). A single best match (no tie at the top score) wins;
otherwise we fall through to creating a new row in the "Importado de
Gesdén" category so the operator can re-classify manually later.

A single ``TreatmentCategory`` keyed ``migrado_gesden`` is lazily
created per clinic on the first newly-created import.

``internal_code`` uses the source canonical UUID's first 8 chars
prefixed with ``MIG-`` instead of the raw Gesdén code, because the
source can carry duplicate codes (e.g. multiple tariff variants share
a code) which would violate the catalog's
``uq_catalog_item_clinic_code`` constraint.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import select

from app.modules.catalog.models import TreatmentCatalogItem, TreatmentCategory
from app.modules.catalog.service import CatalogService

from ..models import ImportWarning
from ._gesden_catalog import (
    CATEGORY_MIGRATED,
    category_key_for_tipo_odg,
    clinical_type_for_tipo_odg,
    expand_aliases,
    pricing_strategy_for,
    requires_surfaces_for_tipo_odg,
    scope_for_tipo_odg,
)
from .base import MapperContext

if TYPE_CHECKING:
    from ..models import MappingDecision

_MIGRATED_CATEGORY_KEY = CATEGORY_MIGRATED

# Minimum bidirectional token-prefix coverage for the fuzzy fallback
# to claim a match. 1.0 = every meaningful token on both sides found
# a partner (equality or one is the prefix of the other). 0.8 leaves
# room for a single small-token mismatch in long labels while still
# rejecting cousin treatments ("Corona metal" vs "Corona zirconio").
_FUZZY_MATCH_THRESHOLD = 0.8

# Looser threshold applied when category alignment is verified via
# Gesdén ``IdTipoODG``. A category-compatible candidate at 0.7 is a
# safer bet than a 0.85 cross-category candidate, so the boost only
# kicks in inside the filtered subset (never widening cross-category).
_FUZZY_MATCH_THRESHOLD_WITH_CATEGORY = 0.7

# Tokens shorter than this are dropped from the comparison set so
# filler ("de", "el", "y") and aggressive Gesdén abbreviations ("co",
# "rx") don't false-match through prefix containment.
_MIN_TOKEN_LEN = 3


@dataclass(frozen=True)
class Proposal:
    """Automatic catalog mapping proposal — shared between the
    writing path (``apply``) and the proposals dry-run service.

    Actions:
      - ``link`` — exact normalised match on a single existing item.
      - ``fuzzy_link`` — single best fuzzy candidate above threshold.
      - ``create`` — no match; new item lands in ``target_category_key``.
    """

    action: str
    target_id: UUID | None
    target_label: str | None
    target_category_key: str | None
    score: float | None


def _normalise(text: str | None) -> str:
    """Lower-case, accent-strip, punctuation-strip, collapse whitespace.

    Used both for exact comparison and as input to token matching.
    NFKD splits accented characters into base + combining mark; the
    combining marks are then dropped. Punctuation (``.``, ``-``, etc.)
    becomes whitespace so "obtur. comp." collapses to "obtur comp".
    """
    if not text:
        return ""
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    no_punct = re.sub(r"[^\w\s]", " ", stripped.lower())
    return re.sub(r"\s+", " ", no_punct).strip()


def _meaningful_tokens(normalised: str) -> list[str]:
    return [tok for tok in normalised.split() if len(tok) >= _MIN_TOKEN_LEN]


def _token_match_score(src_norm: str, dst_norm: str) -> float:
    """Bidirectional token-prefix coverage between two normalised labels.

    For each meaningful token on one side, look for an equal or
    prefix-related token on the other. The score is the minimum of
    the two directional coverages, so a short Gesdén label like
    "corona metal" does NOT win against the longer destination
    "corona metal cerámica" — the extra "ceramica" token on the
    destination drops dst-coverage and the min penalises the pair.

    Prefix containment in EITHER direction matches the abbreviation
    flavour Gesdén ships: "obtur" ↔ "obturacion", "uni" ↔
    "unirradicular", "zirc" ↔ "zirconio". Filler tokens (< 3 chars)
    are filtered out so "de", "y", "el" don't cause false hits.
    """
    s_tokens = _meaningful_tokens(src_norm)
    d_tokens = _meaningful_tokens(dst_norm)
    if not s_tokens or not d_tokens:
        return 0.0

    def _coverage(a_tokens: list[str], b_tokens: list[str]) -> float:
        matched = 0
        for at in a_tokens:
            for bt in b_tokens:
                if at == bt or at.startswith(bt) or bt.startswith(at):
                    matched += 1
                    break
        return matched / len(a_tokens)

    return min(_coverage(s_tokens, d_tokens), _coverage(d_tokens, s_tokens))


def _is_token_subset(small_norm: str, large_norm: str) -> bool:
    """``True`` when every meaningful token in ``small_norm`` appears in
    ``large_norm`` (equal or in a prefix-relationship in either direction).

    Both sides must carry at least two meaningful tokens. The two-token
    floor avoids latching a bare "corona" / "endodoncia" onto every
    crown / endo variant in the seed: the subset rule needs at least
    two corroborating tokens to claim a match.
    """
    s_tokens = _meaningful_tokens(small_norm)
    l_tokens = _meaningful_tokens(large_norm)
    if len(s_tokens) < 2 or len(l_tokens) < 2:
        return False
    for st in s_tokens:
        if not any(st == lt or st.startswith(lt) or lt.startswith(st) for lt in l_tokens):
            return False
    return True


class CatalogItemMapper:
    def __init__(self) -> None:
        # Lazy per-process cache so repeated import jobs in the same
        # backend don't re-query the category on every entity. Keyed by
        # ``(clinic_id, category_key)`` so the migrated catch-all and
        # seed categories (diagnostico, restauradora, …) are cached
        # together — infer-on-create reuses any of them.
        self._category_cache: dict[tuple[UUID, str], UUID] = {}
        # Snapshot of (normalised_name, item_id, original_es_label,
        # category_key) for active catalog items in each clinic. Built
        # once per clinic on first ``_find_match`` call; lets us skip a
        # SELECT per source row and lets the category filter trim
        # candidates without a re-query.
        self._catalog_snapshot: dict[UUID, list[tuple[str, UUID, str, str]]] = {}

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
        existing = await ctx.resolver.get("treatment_catalog_item", canonical_uuid)
        if existing is not None:
            return existing

        # Honour operator decisions captured in the proposals review
        # pass before falling back to the automatic matcher. When no
        # MappingDecision exists for the job (pre-Phase-D flow or
        # operator skipped the review step) we land on the proposal
        # the automatic matcher would have generated anyway.
        decision = await self._load_decision(ctx, canonical_uuid)

        name, tipo_odg, proposal = await self._compute_proposal(
            ctx, payload=payload, raw=raw, source_id=source_id
        )
        effective_action, effective_target_id, effective_category_key = (
            self._resolve_effective_decision(proposal, decision)
        )

        # IGNORED — operator dropped this row. Mark as skipped so re-
        # runs short-circuit and downstream mappers see a clean miss.
        if effective_action == "ignored":
            await ctx.resolver.mark_skipped("treatment_catalog_item", canonical_uuid, source_system)
            ctx.db.add(
                ImportWarning(
                    job_id=ctx.job_id,
                    entity_type="treatment_catalog_item",
                    source_id=source_id,
                    severity="info",
                    code="catalog.operator_ignored",
                    message=f"Operador ignoró el catálogo Gesdén '{name}'.",
                )
            )
            return None

        # LINK / FUZZY_LINK / ACCEPTED-PROPOSAL with a target — reuse
        # the existing item.
        if effective_target_id is not None and effective_action != "create":
            await ctx.resolver.set(
                entity_type="treatment_catalog_item",
                canonical_uuid=canonical_uuid,
                source_system=source_system,
                dentalpin_table="treatment_catalog_items",
                dentalpin_id=effective_target_id,
            )
            code = (
                "catalog.fuzzy_matched"
                if effective_action == "fuzzy_link"
                else "catalog.matched_existing"
            )
            ctx.db.add(
                ImportWarning(
                    job_id=ctx.job_id,
                    entity_type="treatment_catalog_item",
                    source_id=source_id,
                    severity="info",
                    code=code,
                    message=(
                        f"Catálogo Gesdén '{name}' enlazado a DentalPin id={effective_target_id}."
                    ),
                )
            )
            return effective_target_id

        # CREATE path (proposal == create OR operator forced create_new
        # with a specific category).
        return await self._create_inferred_item(
            ctx,
            name=name,
            payload=payload,
            tipo_odg=tipo_odg,
            canonical_uuid=canonical_uuid,
            source_system=source_system,
            override_category_key=effective_category_key,
        )

    # ------------------------------------------------------------------
    # Proposal pipeline — shared between ``apply`` (writing path) and
    # the proposals service (dry-run path).
    # ------------------------------------------------------------------

    async def compute_proposal(
        self,
        ctx: MapperContext,
        *,
        payload: dict[str, Any],
        raw: dict[str, Any],
        source_id: str,
    ) -> tuple[str, int | None, Proposal]:
        """Public entry point for the proposals service. Returns
        ``(display_name, tipo_odg, proposal)`` without persisting.
        """
        return await self._compute_proposal(ctx, payload=payload, raw=raw, source_id=source_id)

    async def _compute_proposal(
        self,
        ctx: MapperContext,
        *,
        payload: dict[str, Any],
        raw: dict[str, Any],
        source_id: str,
    ) -> tuple[str, int | None, Proposal]:
        # Display label order: the canonical spec lists ``short_name``
        # first (Gesdén's ``DescCorta``), then ``description``
        # (``Descrip``), then ``agenda_description`` (``DescAgenda``).
        # ``name`` is not in the v0.1 spec but we accept it for
        # adapters that emit a generic label — falling all the way to
        # ``code`` produces clinic UIs full of "COD001" entries which
        # the user cannot recognise.
        name = (
            payload.get("short_name")
            or payload.get("description")
            or payload.get("patient_facing_description")
            or payload.get("agenda_description")
            or payload.get("name")
            or payload.get("code")
            or source_id
        )

        # Gesdén ``Tratamientos.IdTipoODG`` (the 46-value odontogram
        # type master) is the strongest category signal we have. The
        # extractor preserves the column name verbatim in raw, but
        # different transformers historically used ``IdTipoOdg`` /
        # ``IdTipoODG`` casings — accept both so this mapper survives
        # either capitalisation.
        tipo_odg = _coerce_int(raw.get("IdTipoODG"))
        if tipo_odg is None:
            tipo_odg = _coerce_int(raw.get("IdTipoOdg"))
        target_category_key: str | None = (
            category_key_for_tipo_odg(tipo_odg) if tipo_odg is not None else None
        )
        # Don't constrain the search to the catch-all category: when
        # IdTipoODG resolves to ``migrado_gesden`` we genuinely don't
        # know the clinical bucket, so leave the search open across
        # the full snapshot.
        category_filter: str | None = (
            target_category_key
            if target_category_key and target_category_key != CATEGORY_MIGRATED
            else None
        )

        match = await self._find_match(ctx, name, category_filter)
        infer_category_key = target_category_key or CATEGORY_MIGRATED
        if match is not None:
            matched_id, matched_label, was_fuzzy = match
            return (
                name,
                tipo_odg,
                Proposal(
                    action="fuzzy_link" if was_fuzzy else "link",
                    target_id=matched_id,
                    target_label=matched_label,
                    target_category_key=None,
                    score=1.0 if not was_fuzzy else None,
                ),
            )
        return (
            name,
            tipo_odg,
            Proposal(
                action="create",
                target_id=None,
                target_label=None,
                target_category_key=infer_category_key,
                score=None,
            ),
        )

    async def _create_inferred_item(
        self,
        ctx: MapperContext,
        *,
        name: str,
        payload: dict[str, Any],
        tipo_odg: int | None,
        canonical_uuid: str,
        source_system: str,
        override_category_key: str | None = None,
    ) -> UUID:
        """Materialise a new ``TreatmentCatalogItem`` for an unmatched
        Gesdén row. Uses the IdTipoODG signal to infer category, scope,
        surfaces and clinical type. ``override_category_key`` lets the
        operator force a different category from the proposals UI.
        """
        target_category_key = (
            override_category_key
            or (category_key_for_tipo_odg(tipo_odg) if tipo_odg is not None else None)
            or CATEGORY_MIGRATED
        )
        category_id = await self._get_or_create_category(ctx, target_category_key)
        internal_code = f"MIG-{canonical_uuid[:8]}"
        price = _decimal_or_none(payload.get("reference_price"))
        duration = payload.get("duration_minutes")

        scope = scope_for_tipo_odg(tipo_odg)
        clinical_type = clinical_type_for_tipo_odg(tipo_odg)
        needs_surfaces = requires_surfaces_for_tipo_odg(tipo_odg)
        pricing_strategy = pricing_strategy_for(tipo_odg, clinical_type, needs_surfaces)

        data: dict[str, Any] = {
            "category_id": category_id,
            "internal_code": internal_code,
            "names": {"es": str(name)[:200]},
            "default_price": price,
            "default_duration_minutes": int(duration) if duration else None,
            "requires_appointment": True,
            "pricing_strategy": pricing_strategy,
            "treatment_scope": scope,
            "is_diagnostic": False,
            "requires_surfaces": needs_surfaces,
            "billing_mode": "on_completion",
            "is_active": not bool(payload.get("deactivated", False)),
        }
        if clinical_type is not None:
            # Nested mapping payload — CatalogService.create_item knows
            # how to pop this and create the sibling
            # TreatmentOdontogramMapping row. Visualization rules are
            # left empty for inferred items; the operator can fill them
            # in via the catalog UI once they've reclassified the row.
            data["odontogram_mapping"] = {
                "odontogram_treatment_type": clinical_type,
                "visualization_rules": [],
                "visualization_config": {},
                "clinical_category": target_category_key,
            }
        data = {k: v for k, v in data.items() if v is not None}

        item = await CatalogService.create_item(ctx.db, ctx.clinic_id, data)
        await ctx.resolver.set(
            entity_type="treatment_catalog_item",
            canonical_uuid=canonical_uuid,
            source_system=source_system,
            dentalpin_table="treatment_catalog_items",
            dentalpin_id=item.id,
        )
        return item.id

    async def _load_decision(
        self, ctx: MapperContext, canonical_uuid: str
    ) -> MappingDecision | None:
        from ..models import (
            MappingDecision,  # noqa: PLC0415 — runtime import keeps the module decoupled
        )

        result = await ctx.db.execute(
            select(MappingDecision).where(
                MappingDecision.job_id == ctx.job_id,
                MappingDecision.entity_type == "treatment_catalog_item",
                MappingDecision.canonical_uuid == canonical_uuid,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _resolve_effective_decision(
        proposal: Proposal,
        decision: MappingDecision | None,
    ) -> tuple[str, UUID | None, str | None]:
        """Combine the automatic proposal with an operator override.

        Returns ``(action, target_id, category_key)`` ready for the
        write path. When no operator decision exists, the proposal
        wins verbatim — pre-Phase-D jobs and operators who skipped
        the review step land here.
        """
        if decision is None or decision.operator_action == "pending":
            return proposal.action, proposal.target_id, proposal.target_category_key
        if decision.operator_action == "accepted":
            # Use whatever the proposal proposed (re-fired via the row
            # snapshot in case the DB-state changed since proposal-build).
            return proposal.action, proposal.target_id, proposal.target_category_key
        if decision.operator_action == "relinked":
            return "link", decision.operator_target_id, None
        if decision.operator_action == "create_new":
            return "create", None, decision.operator_target_category_key
        if decision.operator_action == "ignored":
            return "ignored", None, None
        # Unknown action — defer to the proposal so we never lose a row.
        return proposal.action, proposal.target_id, proposal.target_category_key

    async def _find_match(
        self,
        ctx: MapperContext,
        name: str,
        category_filter: str | None,
    ) -> tuple[UUID, str, bool] | None:
        """Return ``(id, matched_es_name, was_fuzzy)`` for the best
        DentalPin catalog item match, or ``None`` when no acceptable
        candidate exists.

        Matching strategy:
        1. Normalise (accents stripped, lower-case, punctuation →
           whitespace, whitespace collapsed).
        2. If ``category_filter`` is supplied (Gesdén ``IdTipoODG``
           resolved to a seeded DentalPin category), restrict the
           candidate set to that category. A 0.7 hit inside the right
           bucket beats a 0.85 cross-category hit, so we apply the
           looser ``_FUZZY_MATCH_THRESHOLD_WITH_CATEGORY`` here.
        3. Exact normalised hit on a single candidate → unambiguous
           win.
        4. Otherwise score every active candidate with
           ``_token_match_score``. The source name is also alias-
           expanded (``"corona mc"`` → ``"corona metal ceramica"``)
           and we take the max over both variants so common Gesdén
           short-form labels reach their destination row. The single
           strict-best candidate above the applicable threshold wins;
           ties at the top score fall through.

        Soft-deleted and inactive rows are excluded so we don't
        resurrect retired catalog entries.
        """
        normalised = _normalise(name)
        if len(normalised) < 3:
            return None

        full_snapshot = await self._catalog_snapshot_for_clinic(ctx)
        if not full_snapshot:
            return None

        # Two-pass strategy:
        #   pass 1 (preferred) — category-filtered candidates at the
        #                        looser 0.7 threshold + subset rule
        #   pass 2 (fallback)  — global candidates at the strict 0.8
        #                        threshold, no subset rule
        # The fallback catches Gesdén rows whose operator mis-tagged
        # IdTipoODG (e.g. "SELLADO" under 22-Obturaciones instead of
        # 32-Sellado). Pass 2 only fires when pass 1 returned nothing.
        snapshot = full_snapshot
        threshold = _FUZZY_MATCH_THRESHOLD
        if category_filter is not None:
            filtered = [row for row in full_snapshot if row[3] == category_filter]
            if filtered:
                snapshot = filtered
                threshold = _FUZZY_MATCH_THRESHOLD_WITH_CATEGORY

        exact: list[tuple[UUID, str]] = [
            (item_id, label)
            for norm_name, item_id, label, _cat in snapshot
            if norm_name == normalised
        ]
        if len(exact) == 1:
            return (exact[0][0], exact[0][1], False)
        if len(exact) > 1:
            # Ambiguous — multiple destination items share the same
            # normalised label. Don't pick one at random.
            return None

        # Alias-expanded variant: rewrite Gesdén abbreviations into
        # their long Spanish forms before scoring. The expansion runs
        # over ALL raw tokens (not just meaningful ones) so two-letter
        # codes like ``"mc"`` → ``("metal", "ceramica")`` survive — the
        # ``_meaningful_tokens`` filter would drop them otherwise. The
        # token-match scorer applies the length filter itself, so the
        # space-joined expansion is fed through unchanged.
        raw_tokens = normalised.split()
        expanded_tokens = expand_aliases(raw_tokens)
        expanded_normalised = " ".join(expanded_tokens) if expanded_tokens else normalised

        best_id: UUID | None = None
        best_label = ""
        best_score = 0.0
        tie = False
        # Inside a category-filtered search we also consider the
        # "destination tokens are a subset of source tokens" case as a
        # high-confidence match — Gesdén often appends detail tokens
        # ("OBTURACION COMPOSITE PERMANENTE") that wouldn't otherwise
        # clear the bidirectional threshold. Cross-category searches
        # don't enable this looser rule.
        subset_match: tuple[UUID, str] | None = None
        subset_tie = False
        for norm_name, item_id, label, _cat in snapshot:
            score_a = _token_match_score(normalised, norm_name)
            score_b = (
                _token_match_score(expanded_normalised, norm_name)
                if expanded_normalised != normalised
                else 0.0
            )
            score = max(score_a, score_b)
            if score > best_score:
                best_score = score
                best_id = item_id
                best_label = label
                tie = False
            elif score == best_score and score > 0:
                tie = True
            if category_filter is not None:
                src_for_subset = expanded_normalised or normalised
                # Either direction: src may carry extra detail tokens
                # ("OBTUR COMP PERMANENTE" ⊃ "Obturacion composite") or
                # the seed may carry extra detail ("Reconstruccion
                # estetica composite" ⊃ "Reconstruccion estetica").
                # Both are safe inside the category-bounded search.
                if _is_token_subset(norm_name, src_for_subset) or _is_token_subset(
                    src_for_subset, norm_name
                ):
                    if subset_match is None:
                        subset_match = (item_id, label)
                    elif subset_match[0] != item_id:
                        subset_tie = True
        if best_id is not None and best_score >= threshold and not tie:
            return (best_id, best_label, True)
        # Category-bounded subset fallback — only when no strict score
        # winner exists and there's exactly one item whose tokens are a
        # subset of the source's. Prevents "OBTUR COMP PERMANENTE" from
        # falling into the catch-all when ``REST-COMP`` already exists.
        if subset_match is not None and not subset_tie:
            return (subset_match[0], subset_match[1], True)
        # Global fallback — only runs when the category-filtered pass
        # came up empty. Strict 0.8 threshold, no subset rule. Saves
        # Gesdén rows whose operator filed them under the wrong
        # IdTipoODG: e.g. a sealant filed under 22-Obturaciones still
        # finds PREV-SEAL when we widen the search.
        if category_filter is not None and snapshot is not full_snapshot and best_id is None:
            return await self._global_match(normalised, expanded_normalised, full_snapshot)
        return None

    async def _global_match(
        self,
        normalised: str,
        expanded_normalised: str,
        full_snapshot: list[tuple[str, UUID, str, str]],
    ) -> tuple[UUID, str, bool] | None:
        """Strict-threshold global search across every catalog item.

        Run only as a category-filtered fallback (operator likely
        mis-tagged the source ``IdTipoODG``). Uses the strict 0.8
        threshold for ordinary fuzzy hits, plus a single-winner subset
        rule for the common "Cirugía resectiva" (src) vs "Cirugía
        periodontal resectiva" (dst) case where the Gesdén label omits
        the qualifier tag but the meaning is unambiguous.
        """
        best_id: UUID | None = None
        best_label = ""
        best_score = 0.0
        tie = False
        subset_match: tuple[UUID, str] | None = None
        subset_tie = False
        src_for_subset = expanded_normalised or normalised
        for norm_name, item_id, label, _cat in full_snapshot:
            score_a = _token_match_score(normalised, norm_name)
            score_b = (
                _token_match_score(expanded_normalised, norm_name)
                if expanded_normalised != normalised
                else 0.0
            )
            score = max(score_a, score_b)
            if score > best_score:
                best_score = score
                best_id = item_id
                best_label = label
                tie = False
            elif score == best_score and score > 0:
                tie = True
            if _is_token_subset(norm_name, src_for_subset) or _is_token_subset(
                src_for_subset, norm_name
            ):
                if subset_match is None:
                    subset_match = (item_id, label)
                elif subset_match[0] != item_id:
                    subset_tie = True
        if best_id is not None and best_score >= _FUZZY_MATCH_THRESHOLD and not tie:
            return (best_id, best_label, True)
        if subset_match is not None and not subset_tie:
            return (subset_match[0], subset_match[1], True)
        return None

    async def _catalog_snapshot_for_clinic(
        self, ctx: MapperContext
    ) -> list[tuple[str, UUID, str, str]]:
        """Cache of (normalised_es_name, item_id, original_label,
        category_key) per clinic. Rebuilt on the first call per job.
        The category_key column lets the category filter trim the
        candidate set without re-querying. Inside a single import job
        the destination catalog isn't expected to change under us, so
        snapshotting avoids one SELECT per source Tratamiento.
        """
        cached = self._catalog_snapshot.get(ctx.clinic_id)
        if cached is not None:
            return cached
        result = await ctx.db.execute(
            select(
                TreatmentCatalogItem.id,
                TreatmentCatalogItem.names["es"].astext,
                TreatmentCategory.key,
            )
            .join(TreatmentCategory, TreatmentCategory.id == TreatmentCatalogItem.category_id)
            .where(
                TreatmentCatalogItem.clinic_id == ctx.clinic_id,
                TreatmentCatalogItem.is_active.is_(True),
                TreatmentCatalogItem.deleted_at.is_(None),
            )
        )
        snapshot = [
            (_normalise(label), item_id, label, category_key or "")
            for item_id, label, category_key in result.all()
            if label
        ]
        self._catalog_snapshot[ctx.clinic_id] = snapshot
        return snapshot

    async def _get_or_create_category(self, ctx: MapperContext, category_key: str) -> UUID:
        """Return the destination category id for ``category_key`` in
        ``ctx.clinic_id``. Seed categories (diagnostico, restauradora,
        …) are expected to exist post-bootstrap and are looked up
        directly. The Gesdén catch-all ``migrado_gesden`` is lazily
        created on first use so freshly-seeded clinics don't end up
        with an empty category.
        """
        cache_key = (ctx.clinic_id, category_key)
        if cache_key in self._category_cache:
            return self._category_cache[cache_key]

        result = await ctx.db.execute(
            select(TreatmentCategory.id).where(
                TreatmentCategory.clinic_id == ctx.clinic_id,
                TreatmentCategory.key == category_key,
            )
        )
        category_id = result.scalar_one_or_none()
        if category_id is None:
            if category_key == _MIGRATED_CATEGORY_KEY:
                category = TreatmentCategory(
                    clinic_id=ctx.clinic_id,
                    key=_MIGRATED_CATEGORY_KEY,
                    names={"es": "Importado de Gesdén", "en": "Imported from Gesdén"},
                    display_order=999,
                    is_active=True,
                    is_system=False,
                )
                ctx.db.add(category)
                await ctx.db.flush()
                category_id = category.id
            else:
                # Seed category missing — fall back to the catch-all
                # so we never lose the row. Should only happen on a
                # clinic that skipped ``seed_catalog``.
                return await self._get_or_create_category(ctx, _MIGRATED_CATEGORY_KEY)

        self._category_cache[cache_key] = category_id
        return category_id


def _decimal_or_none(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _coerce_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
