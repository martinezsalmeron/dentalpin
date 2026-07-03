"""`POST /auth/users` must not let an admin inject a membership into a
clinic they don't administer (audit RBAC H1, #95)."""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic


def _payload(clinic_id=None) -> dict:
    body = {
        "email": f"new-{uuid4().hex[:8]}@example.com",
        "password": "TestPass1234",
        "first_name": "New",
        "last_name": "Staff",
        "role": "receptionist",
    }
    if clinic_id is not None:
        body["clinic_id"] = str(clinic_id)
    return body


@pytest.mark.asyncio
async def test_create_user_in_own_clinic_succeeds(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_clinic: Clinic,
) -> None:
    r = await client.post("/api/v1/auth/users", json=_payload(), headers=auth_headers)
    assert r.status_code == 201, r.text


@pytest.mark.asyncio
async def test_create_user_in_foreign_clinic_forbidden(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_clinic: Clinic,
    db_session: AsyncSession,
) -> None:
    # A clinic the caller has no membership in.
    other = Clinic(
        id=uuid4(),
        name="Other Clinic",
        tax_id="B99999999",
        address={"street": "Elsewhere", "city": "Bilbao"},
        settings={},
    )
    db_session.add(other)
    await db_session.commit()

    r = await client.post(
        "/api/v1/auth/users",
        json=_payload(clinic_id=other.id) | {"role": "admin"},
        headers=auth_headers,
    )
    assert r.status_code == 403, r.text
