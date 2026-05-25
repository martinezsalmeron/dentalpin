"""Catalog mapping proposals — review surface between preview and execute.

The catalog mapper used to take its mapping decisions silently in
``execute``: every Gesdén ``treatment_catalog_item`` was either linked
to an existing seed item, fuzzy-matched, or dumped into the
``Importado de Gesdén`` catch-all category — and the operator only
saw the consequences after the import finished. This service surfaces
those decisions ahead of execute so the operator can:

- accept the automatic proposal verbatim (fastest path),
- re-link the Gesdén row to a different DentalPin catalog item,
- force creation of a new row in a specific category, or
- ignore the row entirely (drop it from the import).

The decisions persist in :class:`MappingDecision`. ``execute`` honours
the operator action when present, and falls back to the automatic
matcher otherwise — backward compatible with pre-Phase-D jobs.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .dpmf import open_dpmf
from .mappers.base import MapperContext, MappingResolver
from .mappers.catalog import CatalogItemMapper
from .models import ImportJob, MappingDecision

_PROPOSAL_ENTITY_TYPE = "treatment_catalog_item"


class ProposalsService:
    @staticmethod
    async def build_proposals(
        db: AsyncSession, job: ImportJob, *, passphrase: str | None = None
    ) -> Counter[str]:
        """Idempotently compute proposals for every catalog item in
        the DPMF. Existing decisions are preserved; only rows missing
        a proposal get one written. Returns a counter keyed by
        ``proposed_action`` so the UI can show "link / fuzzy_link /
        create" tallies right after the call.
        """
        # Seed an in-memory cache of canonical_uuids already proposed
        # so we don't double-write on a re-call.
        existing_rows = (
            (
                await db.execute(
                    select(MappingDecision.canonical_uuid).where(
                        MappingDecision.job_id == job.id,
                        MappingDecision.entity_type == _PROPOSAL_ENTITY_TYPE,
                    )
                )
            )
            .scalars()
            .all()
        )
        already_proposed = set(existing_rows)

        # The mapper expects a full MapperContext including a resolver.
        # Proposals run dry, so we use a one-shot resolver scoped to a
        # synthetic id that won't collide with the real execute pass.
        ctx = MapperContext(
            db=db,
            clinic_id=job.clinic_id,
            job_id=job.id,
            resolver=MappingResolver(db=db, clinic_id=job.clinic_id, job_id=job.id),
            import_fiscal_compliance=False,
            created_by=job.created_by,
        )
        mapper = CatalogItemMapper()
        action_counts: Counter[str] = Counter()

        with open_dpmf(Path(job.file_path), passphrase=passphrase) as handle:
            for row in handle.entity_iter(_PROPOSAL_ENTITY_TYPE):
                canonical_uuid, source_id, _src_system, payload_json, raw_json, _ts = row
                if canonical_uuid in already_proposed:
                    # Still count the existing one toward the summary
                    # so the caller sees the full tally on re-build.
                    existing = await db.execute(
                        select(MappingDecision.proposed_action).where(
                            MappingDecision.job_id == job.id,
                            MappingDecision.entity_type == _PROPOSAL_ENTITY_TYPE,
                            MappingDecision.canonical_uuid == canonical_uuid,
                        )
                    )
                    prev_action = existing.scalar_one_or_none()
                    if prev_action:
                        action_counts[prev_action] += 1
                    continue

                try:
                    payload = json.loads(payload_json) if payload_json else {}
                except json.JSONDecodeError:
                    payload = {}
                try:
                    raw = json.loads(raw_json) if raw_json else {}
                except json.JSONDecodeError:
                    raw = {}

                display_name, tipo_odg, proposal = await mapper.compute_proposal(
                    ctx, payload=payload, raw=raw, source_id=source_id
                )

                decision = MappingDecision(
                    job_id=job.id,
                    clinic_id=job.clinic_id,
                    entity_type=_PROPOSAL_ENTITY_TYPE,
                    canonical_uuid=canonical_uuid,
                    source_label=str(display_name)[:255],
                    source_code=_short_code(raw.get("Codigo")),
                    source_tipo_odg=tipo_odg,
                    proposed_action=proposal.action,
                    proposed_target_id=proposal.target_id,
                    proposed_target_label=(
                        proposal.target_label[:255] if proposal.target_label else None
                    ),
                    proposed_target_category_key=proposal.target_category_key,
                    proposed_score=proposal.score,
                    operator_action="pending",
                )
                db.add(decision)
                action_counts[proposal.action] += 1

        await db.flush()
        return action_counts

    @staticmethod
    async def list_proposals(
        db: AsyncSession,
        job_id: UUID,
        *,
        page: int = 1,
        page_size: int = 50,
        operator_action: str | None = None,
        proposed_action: str | None = None,
    ) -> tuple[list[MappingDecision], int]:
        """Paginated read of the proposals for the proposals page."""
        from sqlalchemy import func

        base_filters = [MappingDecision.job_id == job_id]
        if operator_action is not None:
            base_filters.append(MappingDecision.operator_action == operator_action)
        if proposed_action is not None:
            base_filters.append(MappingDecision.proposed_action == proposed_action)

        total = (
            await db.execute(select(func.count(MappingDecision.id)).where(*base_filters))
        ).scalar_one()
        result = await db.execute(
            select(MappingDecision)
            .where(*base_filters)
            .order_by(MappingDecision.operator_action, MappingDecision.source_label)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), int(total or 0)

    @staticmethod
    async def update_decision(
        db: AsyncSession,
        job_id: UUID,
        canonical_uuid: str,
        *,
        operator_action: str,
        operator_target_id: UUID | None,
        operator_target_category_key: str | None,
        operator_notes: str | None,
    ) -> MappingDecision | None:
        """PATCH endpoint backend. Idempotent: re-sending the same
        decision is a no-op."""
        valid = {"pending", "accepted", "relinked", "create_new", "ignored"}
        if operator_action not in valid:
            raise ValueError(f"operator_action must be one of {sorted(valid)}")

        result = await db.execute(
            select(MappingDecision).where(
                MappingDecision.job_id == job_id,
                MappingDecision.canonical_uuid == canonical_uuid,
            )
        )
        decision = result.scalar_one_or_none()
        if decision is None:
            return None

        decision.operator_action = operator_action
        decision.operator_target_id = operator_target_id if operator_action == "relinked" else None
        decision.operator_target_category_key = (
            operator_target_category_key if operator_action == "create_new" else None
        )
        decision.operator_notes = operator_notes
        decision.decided_at = datetime.now(UTC)
        await db.flush()
        return decision

    @staticmethod
    async def bulk_accept(
        db: AsyncSession,
        job_id: UUID,
        *,
        min_score: float = 0.9,
        include_exact: bool = True,
    ) -> int:
        """Set ``operator_action='accepted'`` for every pending
        proposal whose score clears ``min_score``. Exact-link
        proposals (no score because the normalised label matched
        verbatim) are included when ``include_exact`` is true.
        """
        score_clause = MappingDecision.proposed_score >= min_score
        action_filters: list[Any] = [
            (MappingDecision.proposed_action == "fuzzy_link") & score_clause,
        ]
        if include_exact:
            action_filters.append(MappingDecision.proposed_action == "link")

        from sqlalchemy import or_

        result = await db.execute(
            update(MappingDecision)
            .where(
                MappingDecision.job_id == job_id,
                MappingDecision.operator_action == "pending",
                or_(*action_filters),
            )
            .values(operator_action="accepted", decided_at=datetime.now(UTC))
            .execution_options(synchronize_session=False)
        )
        await db.flush()
        return int(result.rowcount or 0)


def _short_code(value: Any) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s[:50] if s else None
