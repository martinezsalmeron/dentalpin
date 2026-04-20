"""Tests for the /api/v1/modules/-/active endpoint.

Covers: response shape, nav filtering by caller role, summary/version
fields populated from the declared manifest.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic, ClinicMembership
from app.core.plugins.service import ModuleService


async def _reconcile(db_session: AsyncSession) -> None:
    await ModuleService(db_session).reconcile_with_db()


async def _register_and_assign(
    client: AsyncClient,
    db_session: AsyncSession,
    *,
    email: str,
    role: str,
) -> str:
    """Register a user, add them to a fresh clinic with ``role``, return token."""
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
        cabinets=[],
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


@pytest.mark.asyncio
async def test_active_shape_for_admin(client: AsyncClient, db_session: AsyncSession) -> None:
    token = await _register_and_assign(
        client, db_session, email="admin-active@example.com", role="admin"
    )
    await _reconcile(db_session)

    response = await client.get(
        "/api/v1/modules/-/active",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    payload = response.json()["data"]

    names = {m["name"] for m in payload}
    # Every declared module should be installed + visible to admin.
    assert {"clinical", "budget", "billing", "treatment_plan", "reports"}.issubset(names)

    billing = next(m for m in payload if m["name"] == "billing")
    assert billing["version"] == "0.1.0"
    assert billing["category"] == "official"
    assert billing["summary"] == "Invoices, payments, credit notes, PDF billing."
    # Admin sees every nav item the billing manifest declares.
    assert any(item["to"] == "/invoices" for item in billing["navigation"])
    assert "billing.read" in billing["permissions"]


@pytest.mark.asyncio
async def test_active_navigation_filtered_for_hygienist(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _register_and_assign(
        client, db_session, email="hyg-active@example.com", role="hygienist"
    )
    await _reconcile(db_session)

    response = await client.get(
        "/api/v1/modules/-/active",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    payload = response.json()["data"]

    by_name = {m["name"]: m for m in payload}

    # Hygienist has patients.read + agenda.appointments.* + budget.read +
    # treatment_plan.plans.read + billing.read — all surface.
    clinical_paths = {item["to"] for item in by_name["clinical"]["navigation"]}
    assert "/" in clinical_paths  # dashboard

    # /appointments nav item is owned by the agenda module (B.2).
    agenda_paths = {item["to"] for item in by_name["agenda"]["navigation"]}
    assert "/appointments" in agenda_paths

    # /patients nav item is owned by the patients module (B.1).
    patients_paths = {item["to"] for item in by_name["patients"]["navigation"]}
    assert "/patients" in patients_paths

    # Reports require reports.billing.read, which hygienist lacks.
    reports_paths = {item["to"] for item in by_name["reports"]["navigation"]}
    assert "/reports" not in reports_paths


@pytest.mark.asyncio
async def test_active_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/modules/-/active")
    assert response.status_code in (401, 403)
