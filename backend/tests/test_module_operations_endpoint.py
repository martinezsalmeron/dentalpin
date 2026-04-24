"""Tests for GET /api/v1/modules/{name}/-/operations."""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic, ClinicMembership
from app.core.plugins.db_models import ModuleOperationLog, ModuleRecord
from app.core.plugins.service import ModuleService
from app.core.plugins.state import ModuleState


async def _reconcile(db_session: AsyncSession) -> None:
    await ModuleService(db_session).reconcile_with_db()


async def _register_and_assign(
    client: AsyncClient,
    db_session: AsyncSession,
    *,
    email: str,
    role: str,
) -> str:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPass1234",
            "first_name": "Test",
            "last_name": "User",
        },
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    user_id = me.json()["data"]["user"]["id"]

    clinic = Clinic(
        id=uuid4(),
        name=f"Test Clinic for {role}",
        tax_id=f"B{uuid4().int % 100_000_000:08d}",
        address={"street": "Test St"},
        settings={},
    )
    db_session.add(clinic)
    await db_session.flush()

    membership = ClinicMembership(
        id=uuid4(),
        user_id=user_id,
        clinic_id=clinic.id,
        role=role,
    )
    db_session.add(membership)
    await db_session.commit()

    return token


async def _seed_log_rows(db_session: AsyncSession, module_name: str, count: int) -> None:
    for idx in range(count):
        db_session.add(
            ModuleOperationLog(
                module_name=module_name,
                operation="install",
                step=f"step_{idx}",
                status="completed" if idx % 2 == 0 else "failed",
                details={"idx": idx},
            )
        )
    await db_session.commit()


async def _ensure_module(db_session: AsyncSession, name: str) -> None:
    existing = await db_session.get(ModuleRecord, name)
    if existing is not None:
        return
    db_session.add(
        ModuleRecord(
            name=name,
            version="0.1.0",
            state=ModuleState.INSTALLED.value,
            category="official",
            removable=True,
            auto_install=False,
            manifest_snapshot={"name": name, "version": "0.1.0"},
        )
    )
    await db_session.commit()


@pytest.mark.asyncio
async def test_operations_returns_recent_entries_desc(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _register_and_assign(
        client, db_session, email="ops-admin@example.com", role="admin"
    )
    await _reconcile(db_session)
    await _ensure_module(db_session, "patients")
    await _seed_log_rows(db_session, "patients", 5)

    response = await client.get(
        "/api/v1/modules/patients/-/operations",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 5
    # Desc by id: latest first.
    ids = [row["id"] for row in data]
    assert ids == sorted(ids, reverse=True)
    # Shape.
    row = data[0]
    assert set(row) >= {
        "id",
        "module_name",
        "operation",
        "step",
        "status",
        "details",
        "created_at",
    }
    assert row["module_name"] == "patients"


@pytest.mark.asyncio
async def test_operations_respects_limit_and_clamps(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _register_and_assign(
        client, db_session, email="ops-limit@example.com", role="admin"
    )
    await _reconcile(db_session)
    await _ensure_module(db_session, "patients")
    await _seed_log_rows(db_session, "patients", 30)

    # limit below default
    response = await client.get(
        "/api/v1/modules/patients/-/operations?limit=3",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert len(response.json()["data"]) == 3

    # limit above cap is clamped to 100 (we have 30 rows, so all 30 returned)
    response = await client.get(
        "/api/v1/modules/patients/-/operations?limit=500",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert len(response.json()["data"]) == 30


@pytest.mark.asyncio
async def test_operations_404_on_unknown_module(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _register_and_assign(
        client, db_session, email="ops-404@example.com", role="admin"
    )
    await _reconcile(db_session)

    response = await client.get(
        "/api/v1/modules/does_not_exist/-/operations",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_operations_forbidden_without_admin_permission(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _register_and_assign(
        client, db_session, email="ops-hyg@example.com", role="hygienist"
    )
    await _reconcile(db_session)

    response = await client.get(
        "/api/v1/modules/patients/-/operations",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_operations_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/modules/patients/-/operations")
    assert response.status_code in (401, 403)
