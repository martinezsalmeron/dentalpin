"""Tests for the catalog seeder.

Verifies that the seeded catalog includes globally-scoped treatments (cleaning,
whitening, whole-arch prosthesis, etc.) and that every seeded item uses one of
the four valid `treatment_scope` values.
"""

from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic
from app.modules.catalog.models import TreatmentCatalogItem
from app.modules.catalog.seed import seed_catalog

VALID_SCOPES = {"tooth", "multi_tooth", "global_mouth", "global_arch"}


@pytest.fixture
async def seeded_clinic(db_session: AsyncSession) -> Clinic:
    clinic = Clinic(
        id=uuid4(),
        name="Seed Clinic",
        tax_id="B44444444",
        address={"street": "x", "city": "y"},
        settings={"slot_duration_min": 15},
        cabinets=[{"name": "G1", "color": "#000"}],
    )
    db_session.add(clinic)
    await db_session.flush()
    await seed_catalog(db_session, clinic.id)
    await db_session.commit()
    return clinic


@pytest.mark.asyncio
async def test_seed_creates_global_mouth_items(
    db_session: AsyncSession, seeded_clinic: Clinic
) -> None:
    result = await db_session.execute(
        select(TreatmentCatalogItem).where(
            TreatmentCatalogItem.clinic_id == seeded_clinic.id,
            TreatmentCatalogItem.treatment_scope == "global_mouth",
        )
    )
    items = list(result.scalars().all())
    codes = {i.internal_code for i in items}

    # Essential globals that should always be seeded.
    assert "PREV-CLEAN" in codes
    assert "PREV-FLUOR" in codes
    assert "PREV-CHECKUP" in codes
    assert any(c.startswith("EST-BLAN") for c in codes), (
        "At least one whitening item should be global_mouth"
    )


@pytest.mark.asyncio
async def test_seed_creates_global_arch_items(
    db_session: AsyncSession, seeded_clinic: Clinic
) -> None:
    result = await db_session.execute(
        select(TreatmentCatalogItem).where(
            TreatmentCatalogItem.clinic_id == seeded_clinic.id,
            TreatmentCatalogItem.treatment_scope == "global_arch",
        )
    )
    items = list(result.scalars().all())
    codes = {i.internal_code for i in items}

    assert "REST-SPLINT-OCC" in codes
    assert "PROT-FULL-SUP" in codes
    assert "PROT-FULL-INF" in codes


@pytest.mark.asyncio
async def test_seed_creates_multi_tooth_items(
    db_session: AsyncSession, seeded_clinic: Clinic
) -> None:
    result = await db_session.execute(
        select(TreatmentCatalogItem).where(
            TreatmentCatalogItem.clinic_id == seeded_clinic.id,
            TreatmentCatalogItem.treatment_scope == "multi_tooth",
        )
    )
    items = list(result.scalars().all())
    codes = {i.internal_code for i in items}

    # All bridges must be multi_tooth.
    assert "REST-BRIDGE-MC" in codes
    assert "REST-BRIDGE-ZIR" in codes


@pytest.mark.asyncio
async def test_seed_items_have_valid_scope(db_session: AsyncSession, seeded_clinic: Clinic) -> None:
    result = await db_session.execute(
        select(TreatmentCatalogItem).where(
            TreatmentCatalogItem.clinic_id == seeded_clinic.id,
        )
    )
    items = list(result.scalars().all())
    assert items, "Seeder should create items"
    for item in items:
        assert item.treatment_scope in VALID_SCOPES, (
            f"{item.internal_code} has invalid scope {item.treatment_scope}"
        )
