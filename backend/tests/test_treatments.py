"""Tests for the unified /treatments API (header + children model)."""

from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic, ClinicMembership
from app.modules.catalog.models import (
    TreatmentCatalogItem,
    TreatmentCategory,
    TreatmentOdontogramMapping,
    VatType,
)


async def _ensure_clinic_and_patient(
    db_session: AsyncSession, client: AsyncClient, auth_headers: dict[str, str]
) -> dict:
    me = await client.get("/api/v1/auth/me", headers=auth_headers)
    user_id = me.json()["data"]["user"]["id"]

    clinic = Clinic(
        id=uuid4(),
        name="Test Clinic",
        tax_id="B99999999",
        address={"street": "x", "city": "y"},
        settings={"slot_duration_min": 15},
        cabinets=[{"name": "G1", "color": "#000"}],
    )
    db_session.add(clinic)
    await db_session.flush()

    db_session.add(
        ClinicMembership(id=uuid4(), user_id=user_id, clinic_id=clinic.id, role="dentist")
    )
    await db_session.commit()

    patient_resp = await client.post(
        "/api/v1/patients",
        headers=auth_headers,
        json={"first_name": "Ana", "last_name": "Perez", "phone": "+34666111222"},
    )
    patient_id = patient_resp.json()["data"]["id"]

    return {"clinic_id": str(clinic.id), "user_id": user_id, "patient_id": patient_id}


async def _seed_catalog_items(db_session: AsyncSession, clinic_id) -> dict:
    """Seed a minimal catalog: a flat filling, a per_tooth crown and a per_role bridge."""
    vat = VatType(clinic_id=clinic_id, names={"es": "Exento"}, rate=0.0, is_default=True)
    db_session.add(vat)
    await db_session.flush()

    cat = TreatmentCategory(
        clinic_id=clinic_id,
        key="restauradora",
        names={"es": "Restauradora"},
        is_system=True,
    )
    db_session.add(cat)
    await db_session.flush()

    filling = TreatmentCatalogItem(
        clinic_id=clinic_id,
        category_id=cat.id,
        internal_code="TST-FILL",
        names={"es": "Empaste"},
        default_price=Decimal("80.00"),
        pricing_strategy="flat",
        treatment_scope="tooth",
        requires_surfaces=True,
        vat_type_id=vat.id,
    )
    crown = TreatmentCatalogItem(
        clinic_id=clinic_id,
        category_id=cat.id,
        internal_code="TST-CROWN",
        names={"es": "Corona"},
        default_price=Decimal("500.00"),
        pricing_strategy="per_tooth",
        treatment_scope="tooth",
        vat_type_id=vat.id,
    )
    bridge = TreatmentCatalogItem(
        clinic_id=clinic_id,
        category_id=cat.id,
        internal_code="TST-BRIDGE",
        names={"es": "Puente"},
        default_price=Decimal("400.00"),
        pricing_strategy="per_role",
        pricing_config={"pillar": 500, "pontic": 300},
        treatment_scope="multi_tooth",
        vat_type_id=vat.id,
    )
    cleaning = TreatmentCatalogItem(
        clinic_id=clinic_id,
        category_id=cat.id,
        internal_code="TST-CLEAN",
        names={"es": "Limpieza"},
        default_price=Decimal("60.00"),
        pricing_strategy="flat",
        treatment_scope="global_mouth",
        vat_type_id=vat.id,
    )
    splint = TreatmentCatalogItem(
        clinic_id=clinic_id,
        category_id=cat.id,
        internal_code="TST-SPLINT-ARCH",
        names={"es": "Férula de descarga"},
        default_price=Decimal("120.00"),
        pricing_strategy="flat",
        treatment_scope="global_arch",
        vat_type_id=vat.id,
    )
    db_session.add_all([filling, crown, bridge, cleaning, splint])
    await db_session.flush()

    for item, otype in (
        (filling, "filling_composite"),
        (crown, "crown"),
        (bridge, "bridge"),
        (cleaning, "caries"),  # arbitrary visual type; cleaning has no dedicated rule
        (splint, "splint"),
    ):
        db_session.add(
            TreatmentOdontogramMapping(
                clinic_id=clinic_id,
                catalog_item_id=item.id,
                odontogram_treatment_type=otype,
                clinical_category="restauradora",
                visualization_rules=[],
                visualization_config={},
            )
        )
    await db_session.commit()

    return {
        "filling_id": str(filling.id),
        "crown_id": str(crown.id),
        "bridge_id": str(bridge.id),
        "cleaning_id": str(cleaning.id),
        "splint_arch_id": str(splint.id),
    }


@pytest.fixture
async def setup(
    db_session: AsyncSession, auth_headers: dict[str, str], client: AsyncClient
) -> dict:
    ctx = await _ensure_clinic_and_patient(db_session, client, auth_headers)
    catalog = await _seed_catalog_items(db_session, ctx["clinic_id"])
    return {**ctx, **catalog}


# ----------------------------------------------------------------------------
# Single-tooth treatments
# ----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_single_tooth_filling_with_surfaces(
    client: AsyncClient, auth_headers: dict, setup: dict
) -> None:
    pid = setup["patient_id"]
    r = await client.post(
        f"/api/v1/odontogram/patients/{pid}/treatments",
        headers=auth_headers,
        json={
            "catalog_item_id": setup["filling_id"],
            "tooth_numbers": [16],
            "surfaces": ["M", "O"],
            "status": "performed",
        },
    )
    assert r.status_code == 201, r.text
    data = r.json()["data"]
    assert data["clinical_type"] == "filling_composite"
    assert data["status"] == "performed"
    assert data["price_snapshot"] == "80.00"
    assert len(data["teeth"]) == 1
    assert data["teeth"][0]["surfaces"] == ["M", "O"]


# ----------------------------------------------------------------------------
# per_tooth pricing (multi-tooth uniform)
# ----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_uniform_multiple_crowns_scales_price(
    client: AsyncClient, auth_headers: dict, setup: dict
) -> None:
    pid = setup["patient_id"]
    r = await client.post(
        f"/api/v1/odontogram/patients/{pid}/treatments",
        headers=auth_headers,
        json={
            "catalog_item_id": setup["crown_id"],
            "scope": "multi_tooth",
            "tooth_numbers": [12, 11, 21, 22],
            "status": "planned",
        },
    )
    assert r.status_code == 201, r.text
    data = r.json()["data"]
    assert data["clinical_type"] == "crown"
    assert len(data["teeth"]) == 4
    assert data["price_snapshot"] == "2000.00"  # 500 * 4


# ----------------------------------------------------------------------------
# per_role pricing (bridges)
# ----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_bridge_assigns_roles_and_prices_per_role(
    client: AsyncClient, auth_headers: dict, setup: dict
) -> None:
    pid = setup["patient_id"]
    r = await client.post(
        f"/api/v1/odontogram/patients/{pid}/treatments",
        headers=auth_headers,
        json={
            "catalog_item_id": setup["bridge_id"],
            "scope": "multi_tooth",
            "tooth_numbers": [14, 15, 16],
            "status": "planned",
        },
    )
    assert r.status_code == 201, r.text
    data = r.json()["data"]
    assert data["clinical_type"] == "bridge"
    by_tooth = {t["tooth_number"]: t["role"] for t in data["teeth"]}
    assert by_tooth == {14: "pillar", 15: "pontic", 16: "pillar"}
    assert Decimal(data["price_snapshot"]) == Decimal("1300")  # 500 + 300 + 500


@pytest.mark.asyncio
async def test_bridge_requires_at_least_two_teeth(
    client: AsyncClient, auth_headers: dict, setup: dict
) -> None:
    r = await client.post(
        f"/api/v1/odontogram/patients/{setup['patient_id']}/treatments",
        headers=auth_headers,
        json={
            "catalog_item_id": setup["bridge_id"],
            "scope": "multi_tooth",
            "tooth_numbers": [14],
            "status": "planned",
        },
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_bridge_cantilever_two_teeth_with_explicit_roles(
    client: AsyncClient, auth_headers: dict, setup: dict
) -> None:
    """Cantilever bridge: 2 teeth, 1 pillar + 1 pontic — caller supplies roles."""
    pid = setup["patient_id"]
    r = await client.post(
        f"/api/v1/odontogram/patients/{pid}/treatments",
        headers=auth_headers,
        json={
            "catalog_item_id": setup["bridge_id"],
            "scope": "multi_tooth",
            "teeth": [
                {"tooth_number": 14, "role": "pillar"},
                {"tooth_number": 15, "role": "pontic"},
            ],
            "status": "planned",
        },
    )
    assert r.status_code == 201, r.text
    data = r.json()["data"]
    by_tooth = {t["tooth_number"]: t["role"] for t in data["teeth"]}
    assert by_tooth == {14: "pillar", 15: "pontic"}
    assert Decimal(data["price_snapshot"]) == Decimal("800")  # 500 + 300


@pytest.mark.asyncio
async def test_bridge_honors_explicit_mid_span_pillar(
    client: AsyncClient, auth_headers: dict, setup: dict
) -> None:
    """Mid-span pillar bridge: pillar-pontic-pillar-pontic-pillar."""
    pid = setup["patient_id"]
    r = await client.post(
        f"/api/v1/odontogram/patients/{pid}/treatments",
        headers=auth_headers,
        json={
            "catalog_item_id": setup["bridge_id"],
            "scope": "multi_tooth",
            "teeth": [
                {"tooth_number": 14, "role": "pillar"},
                {"tooth_number": 15, "role": "pontic"},
                {"tooth_number": 16, "role": "pillar"},
                {"tooth_number": 17, "role": "pontic"},
                {"tooth_number": 18, "role": "pillar"},
            ],
            "status": "planned",
        },
    )
    assert r.status_code == 201, r.text
    data = r.json()["data"]
    by_tooth = {t["tooth_number"]: t["role"] for t in data["teeth"]}
    assert by_tooth == {14: "pillar", 15: "pontic", 16: "pillar", 17: "pontic", 18: "pillar"}


@pytest.mark.asyncio
async def test_bridge_rejects_all_pontic(
    client: AsyncClient, auth_headers: dict, setup: dict
) -> None:
    pid = setup["patient_id"]
    r = await client.post(
        f"/api/v1/odontogram/patients/{pid}/treatments",
        headers=auth_headers,
        json={
            "catalog_item_id": setup["bridge_id"],
            "scope": "multi_tooth",
            "teeth": [
                {"tooth_number": 14, "role": "pontic"},
                {"tooth_number": 15, "role": "pontic"},
                {"tooth_number": 16, "role": "pontic"},
            ],
            "status": "planned",
        },
    )
    assert r.status_code in (400, 422)


# ----------------------------------------------------------------------------
# Diagnostic finding without catalog item
# ----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_diagnostic_finding_without_catalog(
    client: AsyncClient, auth_headers: dict, setup: dict
) -> None:
    r = await client.post(
        f"/api/v1/odontogram/patients/{setup['patient_id']}/treatments",
        headers=auth_headers,
        json={
            "clinical_type": "caries",
            "tooth_numbers": [26],
            "surfaces": ["O"],
            "status": "performed",
        },
    )
    assert r.status_code == 201, r.text
    data = r.json()["data"]
    assert data["clinical_type"] == "caries"
    assert data["catalog_item_id"] is None
    assert data["price_snapshot"] is None


# ----------------------------------------------------------------------------
# Conflicts and validators
# ----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_catalog_clinical_type_conflict_rejected(
    client: AsyncClient, auth_headers: dict, setup: dict
) -> None:
    """If both catalog and clinical_type are given, they must match."""
    r = await client.post(
        f"/api/v1/odontogram/patients/{setup['patient_id']}/treatments",
        headers=auth_headers,
        json={
            "catalog_item_id": setup["crown_id"],
            "clinical_type": "filling_composite",
            "tooth_numbers": [21],
            "status": "planned",
        },
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_perform_transitions_status(
    client: AsyncClient, auth_headers: dict, setup: dict
) -> None:
    pid = setup["patient_id"]
    create = await client.post(
        f"/api/v1/odontogram/patients/{pid}/treatments",
        headers=auth_headers,
        json={
            "catalog_item_id": setup["crown_id"],
            "tooth_numbers": [26],
            "status": "planned",
        },
    )
    tid = create.json()["data"]["id"]
    r = await client.patch(
        f"/api/v1/odontogram/treatments/{tid}/perform",
        headers=auth_headers,
        json={"notes": "done"},
    )
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "performed"


@pytest.mark.asyncio
async def test_delete_soft_deletes(
    client: AsyncClient, auth_headers: dict, setup: dict, db_session: AsyncSession
) -> None:
    pid = setup["patient_id"]
    create = await client.post(
        f"/api/v1/odontogram/patients/{pid}/treatments",
        headers=auth_headers,
        json={
            "catalog_item_id": setup["crown_id"],
            "tooth_numbers": [26],
            "status": "planned",
        },
    )
    tid = create.json()["data"]["id"]
    r = await client.delete(f"/api/v1/odontogram/treatments/{tid}", headers=auth_headers)
    assert r.status_code == 204

    listing = await client.get(
        f"/api/v1/odontogram/patients/{pid}/treatments", headers=auth_headers
    )
    assert listing.json()["total"] == 0  # soft-deleted excluded


# ----------------------------------------------------------------------------
# scope derivation and global treatments
# ----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_scope_tooth_derived_from_single_tooth(
    client: AsyncClient, auth_headers: dict, setup: dict
) -> None:
    pid = setup["patient_id"]
    r = await client.post(
        f"/api/v1/odontogram/patients/{pid}/treatments",
        headers=auth_headers,
        json={
            "catalog_item_id": setup["crown_id"],
            "tooth_numbers": [26],
            "status": "planned",
        },
    )
    assert r.status_code == 201, r.text
    data = r.json()["data"]
    assert data["scope"] == "tooth"
    assert data["arch"] is None


@pytest.mark.asyncio
async def test_scope_multi_tooth_derived_when_two_teeth(
    client: AsyncClient, auth_headers: dict, setup: dict
) -> None:
    pid = setup["patient_id"]
    r = await client.post(
        f"/api/v1/odontogram/patients/{pid}/treatments",
        headers=auth_headers,
        json={
            "catalog_item_id": setup["crown_id"],
            "tooth_numbers": [11, 21],
            "status": "planned",
        },
    )
    assert r.status_code == 201, r.text
    assert r.json()["data"]["scope"] == "multi_tooth"


@pytest.mark.asyncio
async def test_create_global_mouth_treatment(
    client: AsyncClient, auth_headers: dict, setup: dict
) -> None:
    pid = setup["patient_id"]
    r = await client.post(
        f"/api/v1/odontogram/patients/{pid}/treatments",
        headers=auth_headers,
        json={
            "catalog_item_id": setup["cleaning_id"],
            "scope": "global_mouth",
            "status": "planned",
        },
    )
    assert r.status_code == 201, r.text
    data = r.json()["data"]
    assert data["scope"] == "global_mouth"
    assert data["arch"] is None
    assert data["teeth"] == []
    assert data["price_snapshot"] == "60.00"


@pytest.mark.asyncio
async def test_create_global_arch_treatment(
    client: AsyncClient, auth_headers: dict, setup: dict
) -> None:
    pid = setup["patient_id"]
    r = await client.post(
        f"/api/v1/odontogram/patients/{pid}/treatments",
        headers=auth_headers,
        json={
            "catalog_item_id": setup["splint_arch_id"],
            "scope": "global_arch",
            "arch": "upper",
            "status": "planned",
        },
    )
    assert r.status_code == 201, r.text
    data = r.json()["data"]
    assert data["scope"] == "global_arch"
    assert data["arch"] == "upper"
    assert data["teeth"] == []


@pytest.mark.asyncio
async def test_global_arch_requires_arch(
    client: AsyncClient, auth_headers: dict, setup: dict
) -> None:
    pid = setup["patient_id"]
    r = await client.post(
        f"/api/v1/odontogram/patients/{pid}/treatments",
        headers=auth_headers,
        json={
            "catalog_item_id": setup["splint_arch_id"],
            "scope": "global_arch",
            "status": "planned",
        },
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_arch_rejected_for_non_global_arch_scope(
    client: AsyncClient, auth_headers: dict, setup: dict
) -> None:
    pid = setup["patient_id"]
    r = await client.post(
        f"/api/v1/odontogram/patients/{pid}/treatments",
        headers=auth_headers,
        json={
            "catalog_item_id": setup["crown_id"],
            "tooth_numbers": [26],
            "arch": "upper",
            "status": "planned",
        },
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_global_mouth_rejects_teeth(
    client: AsyncClient, auth_headers: dict, setup: dict
) -> None:
    pid = setup["patient_id"]
    r = await client.post(
        f"/api/v1/odontogram/patients/{pid}/treatments",
        headers=auth_headers,
        json={
            "catalog_item_id": setup["cleaning_id"],
            "scope": "global_mouth",
            "tooth_numbers": [11],
            "status": "planned",
        },
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_no_scope_no_teeth_raises(
    client: AsyncClient, auth_headers: dict, setup: dict
) -> None:
    pid = setup["patient_id"]
    r = await client.post(
        f"/api/v1/odontogram/patients/{pid}/treatments",
        headers=auth_headers,
        json={
            "catalog_item_id": setup["crown_id"],
            "status": "planned",
        },
    )
    assert r.status_code == 422
