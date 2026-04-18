"""Tests for the catalog module."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic, ClinicMembership
from app.modules.catalog.models import VatType


@pytest.fixture
async def catalog_clinic_setup(
    db_session: AsyncSession, auth_headers: dict[str, str], client: AsyncClient
) -> dict:
    """Set up a clinic with the test user as admin for catalog tests."""
    # Get user from /me endpoint
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    user_id = response.json()["data"]["user"]["id"]

    # Create clinic
    clinic = Clinic(
        id=uuid4(),
        name="Catalog Test Clinic",
        tax_id="B87654321",
        address={"street": "Catalog St", "city": "Madrid"},
        settings={"slot_duration_min": 15},
        cabinets=[{"name": "Gabinete 1", "color": "#3B82F6"}],
    )
    db_session.add(clinic)
    await db_session.flush()

    # Create admin membership
    membership = ClinicMembership(
        id=uuid4(),
        user_id=user_id,
        clinic_id=clinic.id,
        role="admin",
    )
    db_session.add(membership)

    # Create default VAT types for the clinic
    vat_exempt = VatType(
        id=uuid4(),
        clinic_id=clinic.id,
        names={"es": "Exento", "en": "Exempt"},
        rate=0.0,
        is_default=True,
        is_system=True,
    )
    vat_reduced = VatType(
        id=uuid4(),
        clinic_id=clinic.id,
        names={"es": "Reducido (10%)", "en": "Reduced (10%)"},
        rate=10.0,
        is_default=False,
        is_system=True,
    )
    vat_standard = VatType(
        id=uuid4(),
        clinic_id=clinic.id,
        names={"es": "General (21%)", "en": "Standard (21%)"},
        rate=21.0,
        is_default=False,
        is_system=True,
    )
    db_session.add_all([vat_exempt, vat_reduced, vat_standard])
    await db_session.commit()

    return {
        "clinic_id": str(clinic.id),
        "user_id": user_id,
        "vat_exempt_id": str(vat_exempt.id),
        "vat_reduced_id": str(vat_reduced.id),
        "vat_standard_id": str(vat_standard.id),
    }


@pytest.mark.asyncio
async def test_list_categories(client: AsyncClient, auth_headers: dict, catalog_clinic_setup: dict):
    """Test listing treatment categories."""
    response = await client.get(
        "/api/v1/catalog/categories",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_create_category(client: AsyncClient, auth_headers: dict, catalog_clinic_setup: dict):
    """Test creating a treatment category."""
    response = await client.post(
        "/api/v1/catalog/categories",
        json={
            "key": "test_category",
            "names": {"es": "Categoría de Prueba", "en": "Test Category"},
            "display_order": 100,
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["key"] == "test_category"
    assert data["names"]["es"] == "Categoría de Prueba"
    assert data["names"]["en"] == "Test Category"
    assert data["is_system"] is False


@pytest.mark.asyncio
async def test_create_category_duplicate_key(
    client: AsyncClient, auth_headers: dict, catalog_clinic_setup: dict
):
    """Test that duplicate category keys are rejected."""
    # Create first category
    await client.post(
        "/api/v1/catalog/categories",
        json={
            "key": "duplicate_key",
            "names": {"es": "Primera", "en": "First"},
        },
        headers=auth_headers,
    )

    # Try to create duplicate
    response = await client.post(
        "/api/v1/catalog/categories",
        json={
            "key": "duplicate_key",
            "names": {"es": "Segunda", "en": "Second"},
        },
        headers=auth_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_category(client: AsyncClient, auth_headers: dict, catalog_clinic_setup: dict):
    """Test updating a treatment category."""
    # Create category
    create_response = await client.post(
        "/api/v1/catalog/categories",
        json={
            "key": "update_test",
            "names": {"es": "Original", "en": "Original"},
        },
        headers=auth_headers,
    )
    category_id = create_response.json()["data"]["id"]

    # Update category
    response = await client.put(
        f"/api/v1/catalog/categories/{category_id}",
        json={
            "names": {"es": "Actualizado", "en": "Updated"},
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["names"]["es"] == "Actualizado"
    assert data["names"]["en"] == "Updated"


@pytest.mark.asyncio
async def test_delete_category(client: AsyncClient, auth_headers: dict, catalog_clinic_setup: dict):
    """Test deleting a treatment category."""
    # Create category
    create_response = await client.post(
        "/api/v1/catalog/categories",
        json={
            "key": "delete_test",
            "names": {"es": "Para Borrar", "en": "To Delete"},
        },
        headers=auth_headers,
    )
    category_id = create_response.json()["data"]["id"]

    # Delete category
    response = await client.delete(
        f"/api/v1/catalog/categories/{category_id}",
        headers=auth_headers,
    )
    assert response.status_code == 204

    # Verify it's deleted
    get_response = await client.get(
        f"/api/v1/catalog/categories/{category_id}",
        headers=auth_headers,
    )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_list_catalog_items(
    client: AsyncClient, auth_headers: dict, catalog_clinic_setup: dict
):
    """Test listing catalog items."""
    response = await client.get(
        "/api/v1/catalog/items",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)
    assert "total" in data
    assert "page" in data
    assert "page_size" in data


@pytest.mark.asyncio
async def test_create_catalog_item(
    client: AsyncClient, auth_headers: dict, catalog_clinic_setup: dict
):
    """Test creating a catalog item."""
    # First create a category
    cat_response = await client.post(
        "/api/v1/catalog/categories",
        json={
            "key": "item_test_category",
            "names": {"es": "Categoría", "en": "Category"},
        },
        headers=auth_headers,
    )
    category_id = cat_response.json()["data"]["id"]

    # Create catalog item with VAT type
    response = await client.post(
        "/api/v1/catalog/items",
        json={
            "category_id": category_id,
            "internal_code": "TEST-001",
            "names": {"es": "Tratamiento de Prueba", "en": "Test Treatment"},
            "descriptions": {"es": "Descripción", "en": "Description"},
            "default_price": 100.00,
            "currency": "EUR",
            "vat_type_id": catalog_clinic_setup["vat_exempt_id"],
            "treatment_scope": "tooth",
            "is_diagnostic": False,
            "requires_surfaces": False,
            "requires_appointment": True,
            "default_duration_minutes": 30,
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["internal_code"] == "TEST-001"
    assert data["names"]["es"] == "Tratamiento de Prueba"
    assert float(data["default_price"]) == 100.00
    assert data["vat_type"]["rate"] == 0.0  # Check rate from VatType object
    assert data["vat_type_id"] == catalog_clinic_setup["vat_exempt_id"]
    assert data["is_system"] is False


@pytest.mark.asyncio
async def test_create_catalog_item_duplicate_code(
    client: AsyncClient, auth_headers: dict, catalog_clinic_setup: dict
):
    """Test that duplicate internal codes are rejected."""
    # Create category
    cat_response = await client.post(
        "/api/v1/catalog/categories",
        json={
            "key": "dup_item_category",
            "names": {"es": "Cat", "en": "Cat"},
        },
        headers=auth_headers,
    )
    category_id = cat_response.json()["data"]["id"]

    # Create first item
    await client.post(
        "/api/v1/catalog/items",
        json={
            "category_id": category_id,
            "internal_code": "DUP-001",
            "names": {"es": "Primero", "en": "First"},
            "vat_type_id": catalog_clinic_setup["vat_exempt_id"],
            "treatment_scope": "tooth",
        },
        headers=auth_headers,
    )

    # Try to create duplicate
    response = await client.post(
        "/api/v1/catalog/items",
        json={
            "category_id": category_id,
            "internal_code": "DUP-001",
            "names": {"es": "Segundo", "en": "Second"},
            "vat_type_id": catalog_clinic_setup["vat_exempt_id"],
            "treatment_scope": "tooth",
        },
        headers=auth_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_catalog_item(
    client: AsyncClient, auth_headers: dict, catalog_clinic_setup: dict
):
    """Test getting a single catalog item."""
    # Create category
    cat_response = await client.post(
        "/api/v1/catalog/categories",
        json={
            "key": "get_item_category",
            "names": {"es": "Cat", "en": "Cat"},
        },
        headers=auth_headers,
    )
    category_id = cat_response.json()["data"]["id"]

    # Create item
    create_response = await client.post(
        "/api/v1/catalog/items",
        json={
            "category_id": category_id,
            "internal_code": "GET-001",
            "names": {"es": "Obtener", "en": "Get"},
            "vat_type_id": catalog_clinic_setup["vat_exempt_id"],
            "treatment_scope": "tooth",
        },
        headers=auth_headers,
    )
    item_id = create_response.json()["data"]["id"]

    # Get item
    response = await client.get(
        f"/api/v1/catalog/items/{item_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["internal_code"] == "GET-001"


@pytest.mark.asyncio
async def test_update_catalog_item(
    client: AsyncClient, auth_headers: dict, catalog_clinic_setup: dict
):
    """Test updating a catalog item."""
    # Create category
    cat_response = await client.post(
        "/api/v1/catalog/categories",
        json={
            "key": "update_item_category",
            "names": {"es": "Cat", "en": "Cat"},
        },
        headers=auth_headers,
    )
    category_id = cat_response.json()["data"]["id"]

    # Create item
    create_response = await client.post(
        "/api/v1/catalog/items",
        json={
            "category_id": category_id,
            "internal_code": "UPD-001",
            "names": {"es": "Original", "en": "Original"},
            "default_price": 50.00,
            "vat_type_id": catalog_clinic_setup["vat_exempt_id"],
            "treatment_scope": "tooth",
        },
        headers=auth_headers,
    )
    item_id = create_response.json()["data"]["id"]

    # Update item
    response = await client.put(
        f"/api/v1/catalog/items/{item_id}",
        json={
            "names": {"es": "Actualizado", "en": "Updated"},
            "default_price": 75.00,
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["names"]["es"] == "Actualizado"
    assert float(data["default_price"]) == 75.00


@pytest.mark.asyncio
async def test_delete_catalog_item(
    client: AsyncClient, auth_headers: dict, catalog_clinic_setup: dict
):
    """Test deleting a catalog item (soft delete)."""
    # Create category
    cat_response = await client.post(
        "/api/v1/catalog/categories",
        json={
            "key": "delete_item_category",
            "names": {"es": "Cat", "en": "Cat"},
        },
        headers=auth_headers,
    )
    category_id = cat_response.json()["data"]["id"]

    # Create item
    create_response = await client.post(
        "/api/v1/catalog/items",
        json={
            "category_id": category_id,
            "internal_code": "DEL-001",
            "names": {"es": "Borrar", "en": "Delete"},
            "vat_type_id": catalog_clinic_setup["vat_exempt_id"],
            "treatment_scope": "tooth",
        },
        headers=auth_headers,
    )
    item_id = create_response.json()["data"]["id"]

    # Delete item
    response = await client.delete(
        f"/api/v1/catalog/items/{item_id}",
        headers=auth_headers,
    )
    assert response.status_code == 204

    # Verify it's not in list
    list_response = await client.get(
        "/api/v1/catalog/items",
        headers=auth_headers,
    )
    item_ids = [item["id"] for item in list_response.json()["data"]]
    assert item_id not in item_ids


@pytest.mark.asyncio
async def test_search_catalog_items(
    client: AsyncClient, auth_headers: dict, catalog_clinic_setup: dict
):
    """Test searching catalog items."""
    # Create category
    cat_response = await client.post(
        "/api/v1/catalog/categories",
        json={
            "key": "search_category",
            "names": {"es": "Búsqueda", "en": "Search"},
        },
        headers=auth_headers,
    )
    category_id = cat_response.json()["data"]["id"]

    # Create items
    await client.post(
        "/api/v1/catalog/items",
        json={
            "category_id": category_id,
            "internal_code": "SRCH-CORONA",
            "names": {"es": "Corona Dental", "en": "Dental Crown"},
            "vat_type_id": catalog_clinic_setup["vat_exempt_id"],
            "treatment_scope": "tooth",
        },
        headers=auth_headers,
    )

    await client.post(
        "/api/v1/catalog/items",
        json={
            "category_id": category_id,
            "internal_code": "SRCH-EXTRAC",
            "names": {"es": "Extracción", "en": "Extraction"},
            "vat_type_id": catalog_clinic_setup["vat_exempt_id"],
            "treatment_scope": "tooth",
        },
        headers=auth_headers,
    )

    # Search by code
    response = await client.get(
        "/api/v1/catalog/items/search?q=CORONA",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) >= 1
    assert any("CORONA" in item["internal_code"] for item in data)

    # Search by name
    response = await client.get(
        "/api/v1/catalog/items/search?q=Extrac",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_list_items_with_category_filter(
    client: AsyncClient, auth_headers: dict, catalog_clinic_setup: dict
):
    """Test filtering catalog items by category."""
    # Create two categories
    cat1_response = await client.post(
        "/api/v1/catalog/categories",
        json={
            "key": "filter_cat_1",
            "names": {"es": "Cat 1", "en": "Cat 1"},
        },
        headers=auth_headers,
    )
    cat1_id = cat1_response.json()["data"]["id"]

    cat2_response = await client.post(
        "/api/v1/catalog/categories",
        json={
            "key": "filter_cat_2",
            "names": {"es": "Cat 2", "en": "Cat 2"},
        },
        headers=auth_headers,
    )
    cat2_id = cat2_response.json()["data"]["id"]

    # Create items in each category
    await client.post(
        "/api/v1/catalog/items",
        json={
            "category_id": cat1_id,
            "internal_code": "FILT-CAT1",
            "names": {"es": "En Cat 1", "en": "In Cat 1"},
            "vat_type_id": catalog_clinic_setup["vat_exempt_id"],
            "treatment_scope": "tooth",
        },
        headers=auth_headers,
    )

    await client.post(
        "/api/v1/catalog/items",
        json={
            "category_id": cat2_id,
            "internal_code": "FILT-CAT2",
            "names": {"es": "En Cat 2", "en": "In Cat 2"},
            "vat_type_id": catalog_clinic_setup["vat_exempt_id"],
            "treatment_scope": "tooth",
        },
        headers=auth_headers,
    )

    # Filter by category 1
    response = await client.get(
        f"/api/v1/catalog/items?category_id={cat1_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    # All items should be from category 1
    for item in data:
        if item["internal_code"].startswith("FILT-"):
            assert item["category_id"] == cat1_id


@pytest.mark.asyncio
async def test_get_odontogram_treatments(
    client: AsyncClient, auth_headers: dict, catalog_clinic_setup: dict
):
    """Test getting treatments with odontogram mappings."""
    response = await client.get(
        "/api/v1/catalog/odontogram-treatments",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_get_odontogram_treatments_by_category(
    client: AsyncClient, auth_headers: dict, catalog_clinic_setup: dict
):
    """Test getting odontogram treatments grouped by category."""
    response = await client.get(
        "/api/v1/catalog/odontogram-treatments/by-category",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], dict)


@pytest.mark.asyncio
async def test_catalog_item_with_odontogram_mapping(
    client: AsyncClient, auth_headers: dict, catalog_clinic_setup: dict
):
    """Test creating a catalog item with odontogram mapping."""
    # Create category
    cat_response = await client.post(
        "/api/v1/catalog/categories",
        json={
            "key": "odonto_test_category",
            "names": {"es": "Odontograma", "en": "Odontogram"},
        },
        headers=auth_headers,
    )
    category_id = cat_response.json()["data"]["id"]

    # Create item with odontogram mapping
    response = await client.post(
        "/api/v1/catalog/items",
        json={
            "category_id": category_id,
            "internal_code": "ODONTO-001",
            "names": {"es": "Con Mapeo", "en": "With Mapping"},
            "vat_type_id": catalog_clinic_setup["vat_exempt_id"],
            "treatment_scope": "tooth",
            "odontogram_mapping": {
                "odontogram_treatment_type": "crown",
                "clinical_category": "restauradora",
                "visualization_rules": [
                    {"layer": "cenital_pattern", "pattern": "outline", "color": "#3B82F6"}
                ],
                "visualization_config": {"color": "#3B82F6"},
            },
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["internal_code"] == "ODONTO-001"
    assert data["odontogram_mapping"] is not None
    assert data["odontogram_mapping"]["odontogram_treatment_type"] == "crown"


@pytest.mark.asyncio
async def test_catalog_requires_authentication(client: AsyncClient):
    """Test that catalog endpoints require authentication."""
    response = await client.get("/api/v1/catalog/items")
    assert response.status_code == 401

    response = await client.get("/api/v1/catalog/categories")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_catalog_item_pagination(
    client: AsyncClient, auth_headers: dict, catalog_clinic_setup: dict
):
    """Test catalog item pagination."""
    # Create category
    cat_response = await client.post(
        "/api/v1/catalog/categories",
        json={
            "key": "pagination_category",
            "names": {"es": "Paginación", "en": "Pagination"},
        },
        headers=auth_headers,
    )
    category_id = cat_response.json()["data"]["id"]

    # Create multiple items
    for i in range(5):
        await client.post(
            "/api/v1/catalog/items",
            json={
                "category_id": category_id,
                "internal_code": f"PAGE-{i:03d}",
                "names": {"es": f"Item {i}", "en": f"Item {i}"},
                "vat_type": "exempt",
                "vat_rate": 0,
                "treatment_scope": "tooth",
            },
            headers=auth_headers,
        )

    # Test pagination
    response = await client.get(
        "/api/v1/catalog/items?page=1&page_size=2",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) <= 2
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total"] >= 5


@pytest.mark.asyncio
async def test_catalog_item_vat_types(
    client: AsyncClient, auth_headers: dict, catalog_clinic_setup: dict
):
    """Test different VAT types for catalog items."""
    # Create category
    cat_response = await client.post(
        "/api/v1/catalog/categories",
        json={
            "key": "vat_category",
            "names": {"es": "IVA", "en": "VAT"},
        },
        headers=auth_headers,
    )
    category_id = cat_response.json()["data"]["id"]

    # Create exempt item (healthcare)
    response = await client.post(
        "/api/v1/catalog/items",
        json={
            "category_id": category_id,
            "internal_code": "VAT-EXEMPT",
            "names": {"es": "Exento", "en": "Exempt"},
            "vat_type_id": catalog_clinic_setup["vat_exempt_id"],
            "treatment_scope": "tooth",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["vat_type_id"] == catalog_clinic_setup["vat_exempt_id"]
    assert data["vat_type"]["rate"] == 0.0
    assert data["vat_type"]["names"]["en"] == "Exempt"

    # Create reduced VAT item
    response = await client.post(
        "/api/v1/catalog/items",
        json={
            "category_id": category_id,
            "internal_code": "VAT-REDUCED",
            "names": {"es": "Reducido", "en": "Reduced"},
            "vat_type_id": catalog_clinic_setup["vat_reduced_id"],
            "treatment_scope": "tooth",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["vat_type_id"] == catalog_clinic_setup["vat_reduced_id"]
    assert data["vat_type"]["rate"] == 10.0

    # Create standard VAT item (cosmetic)
    response = await client.post(
        "/api/v1/catalog/items",
        json={
            "category_id": category_id,
            "internal_code": "VAT-STANDARD",
            "names": {"es": "General", "en": "Standard"},
            "vat_type_id": catalog_clinic_setup["vat_standard_id"],
            "treatment_scope": "tooth",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["vat_type_id"] == catalog_clinic_setup["vat_standard_id"]
    assert data["vat_type"]["rate"] == 21.0


@pytest.mark.asyncio
async def test_catalog_item_treatment_scopes(
    client: AsyncClient, auth_headers: dict, catalog_clinic_setup: dict
):
    """Test different treatment scopes."""
    # Create category
    cat_response = await client.post(
        "/api/v1/catalog/categories",
        json={
            "key": "scope_category",
            "names": {"es": "Alcance", "en": "Scope"},
        },
        headers=auth_headers,
    )
    category_id = cat_response.json()["data"]["id"]

    # Create whole tooth treatment
    response = await client.post(
        "/api/v1/catalog/items",
        json={
            "category_id": category_id,
            "internal_code": "SCOPE-TOOTH",
            "names": {"es": "Diente Completo", "en": "Whole Tooth"},
            "vat_type_id": catalog_clinic_setup["vat_exempt_id"],
            "treatment_scope": "tooth",
            "requires_surfaces": False,
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["data"]["treatment_scope"] == "tooth"
    assert response.json()["data"]["requires_surfaces"] is False

    # Create surface-sensitive tooth treatment (requires_surfaces flag drives per-surface pricing).
    response = await client.post(
        "/api/v1/catalog/items",
        json={
            "category_id": category_id,
            "internal_code": "SCOPE-SURFACE",
            "names": {"es": "Por Superficie", "en": "Per Surface"},
            "vat_type_id": catalog_clinic_setup["vat_exempt_id"],
            "treatment_scope": "tooth",
            "requires_surfaces": True,
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["data"]["treatment_scope"] == "tooth"
    assert response.json()["data"]["requires_surfaces"] is True


# ============================================================================
# VAT Types Management Tests
# ============================================================================


@pytest.mark.asyncio
async def test_list_vat_types(client: AsyncClient, auth_headers: dict, catalog_clinic_setup: dict):
    """Test listing VAT types."""
    response = await client.get(
        "/api/v1/catalog/vat-types",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)
    # Should have the 3 seeded VAT types
    assert len(data["data"]) >= 3


@pytest.mark.asyncio
async def test_get_default_vat_type(
    client: AsyncClient, auth_headers: dict, catalog_clinic_setup: dict
):
    """Test getting the default VAT type."""
    response = await client.get(
        "/api/v1/catalog/vat-types/default",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["is_default"] is True
    assert data["rate"] == 0.0  # Exempt is the default


@pytest.mark.asyncio
async def test_get_vat_type_by_id(
    client: AsyncClient, auth_headers: dict, catalog_clinic_setup: dict
):
    """Test getting a VAT type by ID."""
    vat_type_id = catalog_clinic_setup["vat_exempt_id"]
    response = await client.get(
        f"/api/v1/catalog/vat-types/{vat_type_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == vat_type_id
    assert data["rate"] == 0.0


@pytest.mark.asyncio
async def test_create_vat_type(client: AsyncClient, auth_headers: dict, catalog_clinic_setup: dict):
    """Test creating a new VAT type."""
    response = await client.post(
        "/api/v1/catalog/vat-types",
        json={
            "names": {"es": "Super Reducido", "en": "Super Reduced"},
            "rate": 4.0,
            "is_default": False,
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["names"]["es"] == "Super Reducido"
    assert data["rate"] == 4.0
    assert data["is_default"] is False
    assert data["is_system"] is False


@pytest.mark.asyncio
async def test_update_vat_type(client: AsyncClient, auth_headers: dict, catalog_clinic_setup: dict):
    """Test updating a VAT type."""
    # First create a non-system VAT type
    create_response = await client.post(
        "/api/v1/catalog/vat-types",
        json={
            "names": {"es": "Para Editar", "en": "To Edit"},
            "rate": 5.0,
        },
        headers=auth_headers,
    )
    vat_type_id = create_response.json()["data"]["id"]

    # Update it
    response = await client.put(
        f"/api/v1/catalog/vat-types/{vat_type_id}",
        json={
            "names": {"es": "Editado", "en": "Edited"},
            "rate": 7.0,
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["names"]["es"] == "Editado"
    assert data["rate"] == 7.0


@pytest.mark.asyncio
async def test_delete_vat_type(client: AsyncClient, auth_headers: dict, catalog_clinic_setup: dict):
    """Test deleting (deactivating) a VAT type."""
    # First create a non-system VAT type
    create_response = await client.post(
        "/api/v1/catalog/vat-types",
        json={
            "names": {"es": "Para Eliminar", "en": "To Delete"},
            "rate": 6.0,
        },
        headers=auth_headers,
    )
    vat_type_id = create_response.json()["data"]["id"]

    # Delete it
    response = await client.delete(
        f"/api/v1/catalog/vat-types/{vat_type_id}",
        headers=auth_headers,
    )
    assert response.status_code == 204

    # Verify it's inactive (not visible by default)
    list_response = await client.get(
        "/api/v1/catalog/vat-types",
        headers=auth_headers,
    )
    ids = [vt["id"] for vt in list_response.json()["data"]]
    assert vat_type_id not in ids


@pytest.mark.asyncio
async def test_cannot_delete_system_vat_type(
    client: AsyncClient, auth_headers: dict, catalog_clinic_setup: dict
):
    """Test that system VAT type cannot be deleted."""
    # System VAT types return 403
    vat_type_id = catalog_clinic_setup["vat_exempt_id"]
    response = await client.delete(
        f"/api/v1/catalog/vat-types/{vat_type_id}",
        headers=auth_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_cannot_delete_default_vat_type(
    client: AsyncClient, auth_headers: dict, catalog_clinic_setup: dict
):
    """Test that default VAT type cannot be deleted (even non-system ones)."""
    # Create a non-system VAT type and make it default
    create_response = await client.post(
        "/api/v1/catalog/vat-types",
        json={
            "names": {"es": "Nuevo Por Defecto", "en": "New Default"},
            "rate": 8.0,
            "is_default": True,  # This will make it the new default
        },
        headers=auth_headers,
    )
    vat_type_id = create_response.json()["data"]["id"]
    assert create_response.json()["data"]["is_default"] is True

    # Try to delete the default (non-system) VAT type
    response = await client.delete(
        f"/api/v1/catalog/vat-types/{vat_type_id}",
        headers=auth_headers,
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_setting_new_default_unsets_old(
    client: AsyncClient, auth_headers: dict, catalog_clinic_setup: dict
):
    """Test that setting a new default VAT type unsets the old one."""
    # Set reduced as default
    vat_type_id = catalog_clinic_setup["vat_reduced_id"]
    response = await client.put(
        f"/api/v1/catalog/vat-types/{vat_type_id}",
        json={"is_default": True},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["is_default"] is True

    # Check that exempt is no longer default
    exempt_response = await client.get(
        f"/api/v1/catalog/vat-types/{catalog_clinic_setup['vat_exempt_id']}",
        headers=auth_headers,
    )
    assert exempt_response.json()["data"]["is_default"] is False
