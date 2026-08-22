"""Role permission boundaries for india_gst endpoints.

manifest.role_permissions grants settings.read to every clinical role
(the invoice panels call tax-preview / e-invoice status mid-invoicing),
reports.read to dentist + receptionist, and keeps settings.configure /
catalog.manage admin-only.
"""

from __future__ import annotations

from uuid import uuid4

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic, ClinicMembership, User
from app.modules.india_gst.models import IndiaGstSettings


@pytest_asyncio.fixture
async def role_headers(db_session: AsyncSession, india_gst_clinic: Clinic):
    """Factory: auth headers for a fresh user with the given role."""
    from app.core.auth.service import create_access_token, hash_password

    async def _make(role: str) -> dict[str, str]:
        user = User(
            email=f"{role}-{uuid4().hex[:8]}@example.com",
            password_hash=hash_password("TestPass1234"),
            first_name=role.title(),
            last_name="Test",
        )
        db_session.add(user)
        await db_session.flush()
        db_session.add(
            ClinicMembership(id=uuid4(), user_id=user.id, clinic_id=india_gst_clinic.id, role=role)
        )
        await db_session.commit()
        token = create_access_token(user.id, token_version=user.token_version)
        return {"Authorization": f"Bearer {token}"}

    return _make


async def test_receptionist_reads_settings_and_reports_but_cannot_configure(
    client: AsyncClient, role_headers, india_gst_settings: IndiaGstSettings
):
    headers = await role_headers("receptionist")

    assert (await client.get("/api/v1/india_gst/settings", headers=headers)).status_code == 200
    assert (
        await client.get("/api/v1/india_gst/reports/summary", headers=headers)
    ).status_code == 200
    assert (
        await client.post(
            "/api/v1/india_gst/tax-preview",
            json={"items": [], "place_of_supply": "33"},
            headers=headers,
        )
    ).status_code == 200

    r = await client.put("/api/v1/india_gst/settings", json={"trade_name": "Nope"}, headers=headers)
    assert r.status_code == 403
    r = await client.post("/api/v1/india_gst/catalog-defaults/autoconfigure", headers=headers)
    assert r.status_code == 403


async def test_hygienist_reads_settings_but_not_reports(
    client: AsyncClient, role_headers, india_gst_settings: IndiaGstSettings
):
    headers = await role_headers("hygienist")

    assert (await client.get("/api/v1/india_gst/settings", headers=headers)).status_code == 200
    assert (
        await client.get("/api/v1/india_gst/reports/summary", headers=headers)
    ).status_code == 403
    assert (
        await client.get("/api/v1/india_gst/reports/export", headers=headers)
    ).status_code == 403


async def test_assistant_cannot_manage_catalog(
    client: AsyncClient, role_headers, india_gst_settings: IndiaGstSettings
):
    headers = await role_headers("assistant")

    assert (
        await client.get("/api/v1/india_gst/catalog-defaults", headers=headers)
    ).status_code == 403
    assert (
        await client.post("/api/v1/india_gst/catalog-defaults/autoconfigure", headers=headers)
    ).status_code == 403
