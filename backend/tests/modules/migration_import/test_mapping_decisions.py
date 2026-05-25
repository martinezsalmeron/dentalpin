"""MappingDecision flow — proposal generation, operator overrides, execute honors.

Direct service-level coverage (no HTTP). The router thinly wraps these
calls; the API contract is locked in by integration tests elsewhere.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.auth.models import Clinic, User
from app.modules.catalog.models import TreatmentCatalogItem, TreatmentCategory
from app.modules.catalog.seed import seed_catalog
from app.modules.migration_import.mappers.base import MapperContext, MappingResolver
from app.modules.migration_import.mappers.catalog import CatalogItemMapper
from app.modules.migration_import.models import ImportJob, MappingDecision
from app.modules.migration_import.proposals import ProposalsService


@pytest.mark.asyncio
async def test_mapper_honours_operator_relink(db_session) -> None:
    """When the operator chose ``relinked`` with an explicit target,
    execute must wire the source to THAT id, not the proposal's."""
    clinic, admin = await _bootstrap(db_session)
    ctx = await _ctx(db_session, clinic.id, admin.id)
    mapper = CatalogItemMapper()
    canonical = str(uuid4())

    # Pick two seeded items: a "wrong" auto-proposal target and the
    # "right" operator override.
    seed = await _seeded_pair(db_session, clinic.id, "REST-COMP", "REST-AMAL")
    auto_id, override_id = seed["REST-COMP"], seed["REST-AMAL"]

    # Pre-populate a MappingDecision: operator chose REST-AMAL even
    # though the auto-proposal would land on REST-COMP via the alias.
    decision = MappingDecision(
        job_id=ctx.job_id,
        clinic_id=clinic.id,
        entity_type="treatment_catalog_item",
        canonical_uuid=canonical,
        source_label="OBTUR COMP",
        proposed_action="link",
        proposed_target_id=auto_id,
        operator_action="relinked",
        operator_target_id=override_id,
    )
    db_session.add(decision)
    await db_session.flush()

    result_id = await mapper.apply(
        ctx,
        entity_type="treatment_catalog_item",
        payload={"short_name": "OBTUR COMP"},
        raw={"IdTipoODG": 22},
        canonical_uuid=canonical,
        source_id="100",
        source_system="gesden",
    )
    await db_session.flush()
    assert result_id == override_id


@pytest.mark.asyncio
async def test_mapper_honours_operator_ignored(db_session) -> None:
    """``ignored`` rows are skipped — no resolver mapping, no catalog row."""
    clinic, admin = await _bootstrap(db_session)
    ctx = await _ctx(db_session, clinic.id, admin.id)
    mapper = CatalogItemMapper()
    canonical = str(uuid4())

    decision = MappingDecision(
        job_id=ctx.job_id,
        clinic_id=clinic.id,
        entity_type="treatment_catalog_item",
        canonical_uuid=canonical,
        source_label="Bono junio",
        proposed_action="create",
        proposed_target_category_key="migrado_gesden",
        operator_action="ignored",
    )
    db_session.add(decision)
    await db_session.flush()

    result = await mapper.apply(
        ctx,
        entity_type="treatment_catalog_item",
        payload={"short_name": "Bono junio"},
        raw={"IdTipoODG": 14},
        canonical_uuid=canonical,
        source_id="200",
        source_system="gesden",
    )
    await db_session.flush()
    assert result is None
    # Resolver skip sentinel was recorded
    assert await ctx.resolver.was_skipped("treatment_catalog_item", canonical) is True


@pytest.mark.asyncio
async def test_mapper_honours_operator_create_new_category(db_session) -> None:
    """``create_new`` with ``operator_target_category_key`` forces the
    new row into that category instead of the inferred one."""
    clinic, admin = await _bootstrap(db_session)
    ctx = await _ctx(db_session, clinic.id, admin.id)
    mapper = CatalogItemMapper()
    canonical = str(uuid4())

    decision = MappingDecision(
        job_id=ctx.job_id,
        clinic_id=clinic.id,
        entity_type="treatment_catalog_item",
        canonical_uuid=canonical,
        source_label="Especial Doctor X",
        proposed_action="create",
        proposed_target_category_key="migrado_gesden",
        operator_action="create_new",
        operator_target_category_key="estetica",
    )
    db_session.add(decision)
    await db_session.flush()

    new_id = await mapper.apply(
        ctx,
        entity_type="treatment_catalog_item",
        payload={"short_name": "Especial Doctor X", "reference_price": "100.00"},
        raw={"IdTipoODG": 9999},  # would otherwise drop to migrado_gesden
        canonical_uuid=canonical,
        source_id="300",
        source_system="gesden",
    )
    await db_session.flush()
    item = (
        await db_session.execute(
            select(TreatmentCatalogItem).where(TreatmentCatalogItem.id == new_id)
        )
    ).scalar_one()
    category = (
        await db_session.execute(
            select(TreatmentCategory).where(TreatmentCategory.id == item.category_id)
        )
    ).scalar_one()
    assert category.key == "estetica"


@pytest.mark.asyncio
async def test_update_decision_idempotent(db_session) -> None:
    """Re-issuing the same operator decision is a safe no-op."""
    clinic, admin = await _bootstrap(db_session)
    ctx = await _ctx(db_session, clinic.id, admin.id)
    canonical = str(uuid4())

    db_session.add(
        MappingDecision(
            job_id=ctx.job_id,
            clinic_id=clinic.id,
            entity_type="treatment_catalog_item",
            canonical_uuid=canonical,
            source_label="X",
            proposed_action="create",
            proposed_target_category_key="migrado_gesden",
            operator_action="pending",
        )
    )
    await db_session.flush()

    decision = await ProposalsService.update_decision(
        db_session,
        ctx.job_id,
        canonical,
        operator_action="accepted",
        operator_target_id=None,
        operator_target_category_key=None,
        operator_notes="ok",
    )
    assert decision is not None
    first_decided_at = decision.decided_at

    decision = await ProposalsService.update_decision(
        db_session,
        ctx.job_id,
        canonical,
        operator_action="accepted",
        operator_target_id=None,
        operator_target_category_key=None,
        operator_notes="ok",
    )
    assert decision is not None
    # decided_at refreshes on each call — acceptable for an audit
    # trail. Behaviour-wise the second call is still a safe no-op.
    assert decision.operator_action == "accepted"
    assert decision.decided_at >= first_decided_at


@pytest.mark.asyncio
async def test_update_decision_rejects_unknown_action(db_session) -> None:
    clinic, admin = await _bootstrap(db_session)
    ctx = await _ctx(db_session, clinic.id, admin.id)
    canonical = str(uuid4())

    db_session.add(
        MappingDecision(
            job_id=ctx.job_id,
            clinic_id=clinic.id,
            entity_type="treatment_catalog_item",
            canonical_uuid=canonical,
            source_label="X",
            proposed_action="create",
            proposed_target_category_key="migrado_gesden",
            operator_action="pending",
        )
    )
    await db_session.flush()

    with pytest.raises(ValueError):
        await ProposalsService.update_decision(
            db_session,
            ctx.job_id,
            canonical,
            operator_action="bogus",
            operator_target_id=None,
            operator_target_category_key=None,
            operator_notes=None,
        )


@pytest.mark.asyncio
async def test_bulk_accept_picks_high_confidence_only(db_session) -> None:
    """Default min_score=0.9 must NOT auto-accept low-confidence
    fuzzy matches — those need explicit operator review."""
    clinic, admin = await _bootstrap(db_session)
    ctx = await _ctx(db_session, clinic.id, admin.id)

    db_session.add_all(
        [
            MappingDecision(
                job_id=ctx.job_id,
                clinic_id=clinic.id,
                entity_type="treatment_catalog_item",
                canonical_uuid=str(uuid4()),
                source_label="High confidence",
                proposed_action="fuzzy_link",
                proposed_target_id=uuid4(),
                proposed_score=0.95,
                operator_action="pending",
            ),
            MappingDecision(
                job_id=ctx.job_id,
                clinic_id=clinic.id,
                entity_type="treatment_catalog_item",
                canonical_uuid=str(uuid4()),
                source_label="Border",
                proposed_action="fuzzy_link",
                proposed_target_id=uuid4(),
                proposed_score=0.75,
                operator_action="pending",
            ),
            MappingDecision(
                job_id=ctx.job_id,
                clinic_id=clinic.id,
                entity_type="treatment_catalog_item",
                canonical_uuid=str(uuid4()),
                source_label="Exact",
                proposed_action="link",
                proposed_target_id=uuid4(),
                proposed_score=None,
                operator_action="pending",
            ),
        ]
    )
    await db_session.flush()

    accepted = await ProposalsService.bulk_accept(db_session, ctx.job_id, min_score=0.9)
    # 1 high-confidence fuzzy + 1 exact link
    assert accepted == 2


async def _bootstrap(db_session):
    clinic = Clinic(id=uuid4(), name="C", tax_id=f"B{uuid4().hex[:8]}")
    admin = User(
        id=uuid4(),
        email=f"admin-{uuid4().hex[:8]}@test.local",
        password_hash="x",
        first_name="A",
        last_name="A",
    )
    db_session.add_all([clinic, admin])
    await db_session.flush()
    await seed_catalog(db_session, clinic.id)
    await db_session.flush()
    return clinic, admin


async def _ctx(db_session, clinic_id, admin_id):
    job = ImportJob(
        clinic_id=clinic_id,
        created_by=admin_id,
        status="executing",
        original_filename="t.dpm",
        file_path="/tmp/t.dpm",
        file_size=0,
    )
    db_session.add(job)
    await db_session.flush()
    return MapperContext(
        db=db_session,
        clinic_id=clinic_id,
        job_id=job.id,
        resolver=MappingResolver(db=db_session, clinic_id=clinic_id, job_id=job.id),
        import_fiscal_compliance=False,
        created_by=admin_id,
    )


async def _seeded_pair(db_session, clinic_id, *codes) -> dict[str, uuid4]:
    out: dict[str, object] = {}
    for code in codes:
        item = (
            await db_session.execute(
                select(TreatmentCatalogItem).where(
                    TreatmentCatalogItem.clinic_id == clinic_id,
                    TreatmentCatalogItem.internal_code == code,
                )
            )
        ).scalar_one()
        out[code] = item.id
    return out  # type: ignore[return-value]
