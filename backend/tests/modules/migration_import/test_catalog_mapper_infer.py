"""CatalogItemMapper — IdTipoODG-driven inference + alias matching.

DB-backed coverage of the smarter catalog mapper:

- ``IdTipoODG`` resolves to a destination ``TreatmentCategory``,
  ``treatment_scope``, ``requires_surfaces`` and (when available)
  ``odontogram_treatment_type`` when no fuzzy match is found.
- Alias-expanded source labels (``OBTUR. COMP.``, ``CORONA MC``)
  reach their seeded destination items.
- Category filtering prevents a "Corona" Gesdén label from latching
  onto a periodontal "Corona" lookalike.
- Unknown / null IdTipoODG still produces a viable row in the
  ``migrado_gesden`` catch-all.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.auth.models import Clinic, User
from app.modules.catalog.models import (
    TreatmentCatalogItem,
    TreatmentCategory,
)
from app.modules.catalog.seed import seed_catalog
from app.modules.migration_import.mappers.base import MapperContext, MappingResolver
from app.modules.migration_import.mappers.catalog import CatalogItemMapper
from app.modules.migration_import.models import ImportJob


@pytest.mark.asyncio
async def test_alias_expanded_label_matches_seed_item(db_session) -> None:
    """``OBTUR. COMP.`` (Gesdén abbreviation) must reach
    ``Obturación composite`` in the destination seed via the alias
    expansion, not create a duplicate in ``migrado_gesden``."""
    clinic, admin = await _bootstrap(db_session)
    ctx = await _ctx(db_session, clinic.id, admin.id)
    mapper = CatalogItemMapper()
    canonical = str(uuid4())

    matched_id = await mapper.apply(
        ctx,
        entity_type="treatment_catalog_item",
        payload={
            "short_name": "OBTUR. COMP.",
            "reference_price": "60.00",
        },
        raw={"IdTipoODG": 22},  # Obturaciones
        canonical_uuid=canonical,
        source_id="123",
        source_system="gesden",
    )
    await db_session.flush()

    # Should resolve to the seeded REST-COMP item, not a new migrated row
    rest_comp = (
        await db_session.execute(
            select(TreatmentCatalogItem).where(
                TreatmentCatalogItem.clinic_id == clinic.id,
                TreatmentCatalogItem.internal_code == "REST-COMP",
            )
        )
    ).scalar_one()
    assert matched_id == rest_comp.id


@pytest.mark.asyncio
async def test_category_filter_blocks_cross_category_match(db_session) -> None:
    """A surgery-tagged Gesdén row labelled just ``Corona`` must not
    latch onto restoration ``Corona zirconio`` — the category filter
    excludes it. With no candidate in the surgery bucket, the mapper
    creates a new item in the surgery seed category."""
    clinic, admin = await _bootstrap(db_session)
    ctx = await _ctx(db_session, clinic.id, admin.id)
    mapper = CatalogItemMapper()
    canonical = str(uuid4())

    new_id = await mapper.apply(
        ctx,
        entity_type="treatment_catalog_item",
        payload={"short_name": "Corona quirúrgica", "reference_price": "200.00"},
        raw={"IdTipoODG": 35},  # Cirugía
        canonical_uuid=canonical,
        source_id="456",
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
    # Landed in surgery, not restoration
    assert category.key == "cirugia"
    # And not in the migrated catch-all
    assert category.key != "migrado_gesden"


@pytest.mark.asyncio
async def test_infer_on_create_sets_clinical_type_and_scope(db_session) -> None:
    """When no fuzzy match exists, IdTipoODG fills in clinical_type,
    scope and requires_surfaces — so the new row paints on the
    odontogram instead of disappearing as a global flat row."""
    clinic, admin = await _bootstrap(db_session)
    ctx = await _ctx(db_session, clinic.id, admin.id)
    mapper = CatalogItemMapper()
    canonical = str(uuid4())

    new_id = await mapper.apply(
        ctx,
        entity_type="treatment_catalog_item",
        payload={"short_name": "Empaste raro doctor X", "reference_price": "90.00"},
        raw={"IdTipoODG": 22},  # Obturaciones
        canonical_uuid=canonical,
        source_id="789",
        source_system="gesden",
    )
    await db_session.flush()

    item = (
        await db_session.execute(
            select(TreatmentCatalogItem).where(TreatmentCatalogItem.id == new_id)
        )
    ).scalar_one()
    # Restoration scope/surfaces because IdTipoODG=22 (Obturaciones)
    assert item.treatment_scope == "tooth"
    assert item.requires_surfaces is True
    assert item.pricing_strategy == "per_surface"


@pytest.mark.asyncio
async def test_unknown_tipo_odg_lands_in_migrated_catchall(db_session) -> None:
    """A genuinely unknown IdTipoODG must still produce a viable row,
    landed in ``migrado_gesden`` so the operator can reclassify."""
    clinic, admin = await _bootstrap(db_session)
    ctx = await _ctx(db_session, clinic.id, admin.id)
    mapper = CatalogItemMapper()
    canonical = str(uuid4())

    new_id = await mapper.apply(
        ctx,
        entity_type="treatment_catalog_item",
        payload={"short_name": "Tratamiento legacy ZZZ", "reference_price": "50.00"},
        raw={"IdTipoODG": 9999},  # not in our table
        canonical_uuid=canonical,
        source_id="999",
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
    assert category.key == "migrado_gesden"
    # Safe defaults: tooth scope, no surfaces, flat pricing
    assert item.treatment_scope == "tooth"
    assert item.requires_surfaces is False
    assert item.pricing_strategy == "flat"


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
