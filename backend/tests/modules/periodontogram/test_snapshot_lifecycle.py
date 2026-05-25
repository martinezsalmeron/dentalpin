"""End-to-end snapshot lifecycle tests for the periodontogram module.

Covers PR-2 surface:

- ``POST /draft`` is idempotent and pre-seeds 32 permanent teeth.
- PATCH on tooth and site rows persists and respects partial payloads.
- ``POST /close`` flips state to ``closed`` and freezes editing
  (subsequent PATCH attempts return 409).
- ``DELETE`` only works on drafts; deleting a closed snapshot returns
  409.
- ``GET /timeline`` lists closed snapshots in chronological order.
- Multi-tenancy guard: a snapshot from another clinic returns 404.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.core.auth.models import Clinic
from app.modules.patients.models import Patient

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _open_draft(client: AsyncClient, headers: dict[str, str], patient_id: str) -> dict:
    response = await client.post(
        f"/api/v1/periodontogram/patients/{patient_id}/draft",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


async def test_open_draft_is_idempotent_and_seeds_teeth(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_patient: Patient,
) -> None:
    draft_a = await _open_draft(client, auth_headers, str(test_patient.id))
    draft_b = await _open_draft(client, auth_headers, str(test_patient.id))

    assert draft_a["id"] == draft_b["id"], "draft should be idempotent per patient"
    assert draft_a["status"] == "draft"
    assert draft_a["indices"] is None
    assert {t["tooth_number"] for t in draft_a["teeth"]} == set(range(11, 19)) | set(
        range(21, 29)
    ) | set(range(31, 39)) | set(range(41, 49))


async def test_patch_tooth_and_site_then_close_freezes_state(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_patient: Patient,
) -> None:
    draft = await _open_draft(client, auth_headers, str(test_patient.id))
    snapshot_id = draft["id"]

    # Patch tooth-level metric.
    tooth_response = await client.patch(
        f"/api/v1/periodontogram/snapshots/{snapshot_id}/teeth/16",
        headers=auth_headers,
        json={"mobility": 2, "prognosis": "fair", "furcation_buccal": "II"},
    )
    assert tooth_response.status_code == 200, tooth_response.text
    assert tooth_response.json()["data"]["mobility"] == 2

    # Patch site-level metric (creates row lazily).
    site_response = await client.patch(
        f"/api/v1/periodontogram/snapshots/{snapshot_id}/teeth/16/sites/MV",
        headers=auth_headers,
        json={"probing_depth_mm": 5, "bleeding_on_probing": True, "plaque": True},
    )
    assert site_response.status_code == 200, site_response.text
    site = site_response.json()["data"]
    assert site["site_code"] == "MV"
    assert site["probing_depth_mm"] == 5

    # Close snapshot.
    close_response = await client.post(
        f"/api/v1/periodontogram/snapshots/{snapshot_id}/close",
        headers=auth_headers,
        json={"notes": "Initial periodontal assessment"},
    )
    assert close_response.status_code == 200, close_response.text
    closed = close_response.json()["data"]
    assert closed["status"] == "closed"
    assert closed["closed_at"] is not None
    assert closed["notes"] == "Initial periodontal assessment"

    # Further patches are rejected.
    retry = await client.patch(
        f"/api/v1/periodontogram/snapshots/{snapshot_id}/teeth/16",
        headers=auth_headers,
        json={"mobility": 3},
    )
    assert retry.status_code == 409


async def test_delete_only_works_on_drafts(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_patient: Patient,
) -> None:
    draft = await _open_draft(client, auth_headers, str(test_patient.id))
    snapshot_id = draft["id"]

    # Close, then try to delete.
    close_response = await client.post(
        f"/api/v1/periodontogram/snapshots/{snapshot_id}/close",
        headers=auth_headers,
        json={},
    )
    assert close_response.status_code == 200

    delete_response = await client.delete(
        f"/api/v1/periodontogram/snapshots/{snapshot_id}",
        headers=auth_headers,
    )
    assert delete_response.status_code == 409


async def test_discard_draft_returns_204_and_removes_snapshot(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_patient: Patient,
) -> None:
    draft = await _open_draft(client, auth_headers, str(test_patient.id))
    snapshot_id = draft["id"]

    delete_response = await client.delete(
        f"/api/v1/periodontogram/snapshots/{snapshot_id}",
        headers=auth_headers,
    )
    assert delete_response.status_code == 204

    follow = await client.get(
        f"/api/v1/periodontogram/snapshots/{snapshot_id}",
        headers=auth_headers,
    )
    assert follow.status_code == 404


async def test_timeline_lists_closed_snapshots_with_change_count(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_patient: Patient,
) -> None:
    # Draft → fill a site → close.
    draft = await _open_draft(client, auth_headers, str(test_patient.id))
    snapshot_id = draft["id"]
    await client.patch(
        f"/api/v1/periodontogram/snapshots/{snapshot_id}/teeth/11/sites/V",
        headers=auth_headers,
        json={"probing_depth_mm": 3},
    )
    await client.post(
        f"/api/v1/periodontogram/snapshots/{snapshot_id}/close",
        headers=auth_headers,
        json={},
    )

    response = await client.get(
        f"/api/v1/periodontogram/patients/{test_patient.id}/timeline",
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    body = response.json()["data"]
    assert body["draft"] is None
    assert len(body["dates"]) == 1
    assert body["dates"][0]["change_count"] == 1


async def test_snapshot_from_other_clinic_returns_404(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_patient: Patient,
    db_session,
) -> None:
    # Create a foreign clinic + draft owned by it directly via DB.
    foreign_clinic = Clinic(
        id=uuid4(),
        name="Foreign Clinic",
        tax_id="B99999999",
        address={"street": "Otra", "city": "BCN"},
        settings={},
    )
    db_session.add(foreign_clinic)
    await db_session.flush()

    foreign_patient = Patient(
        id=uuid4(),
        clinic_id=foreign_clinic.id,
        first_name="Foreign",
        last_name="Patient",
    )
    db_session.add(foreign_patient)
    await db_session.flush()

    from datetime import UTC, datetime

    from app.modules.periodontogram.models import PeriodontogramSnapshot

    snap = PeriodontogramSnapshot(
        id=uuid4(),
        clinic_id=foreign_clinic.id,
        patient_id=foreign_patient.id,
        status="draft",
        recorded_at=datetime.now(UTC),
        recorded_by=uuid4(),  # arbitrary — FK is only enforced if we flush against the real DB
    )
    # Skip the FK by attaching to a real user — reuse the test user's id.
    me = await client.get("/api/v1/auth/me", headers=auth_headers)
    snap.recorded_by = me.json()["data"]["user"]["id"]

    db_session.add(snap)
    await db_session.commit()

    response = await client.get(
        f"/api/v1/periodontogram/snapshots/{snap.id}",
        headers=auth_headers,
    )
    # Caller's clinic context never sees the foreign snapshot.
    assert response.status_code == 404
