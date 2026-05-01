"""Recalls router smoke tests.

Cover the API surface a receptionist hits while working a call list:
create + duplicate guard, list, log attempt with auto-transition,
snooze, settings GET/PUT, dashboard stats, do_not_contact filter.

Issue #62.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic
from app.modules.patients.models import Patient


@pytest.mark.asyncio
async def test_create_then_duplicate_guard_updates_existing(
    client: AsyncClient, auth_headers: dict, test_patient: Patient
):
    payload = {
        "patient_id": str(test_patient.id),
        "due_month": "2026-08-01",
        "reason": "hygiene",
        "priority": "normal",
        "reason_note": "first",
    }
    res = await client.post("/api/v1/recalls/", json=payload, headers=auth_headers)
    assert res.status_code == 201, res.text
    first = res.json()["data"]
    assert first["status"] == "pending"
    assert first["due_month"] == "2026-08-01"

    # Same patient + reason + active status → guard updates instead of insert.
    payload2 = {
        **payload,
        "due_month": "2026-09-01",
        "priority": "high",
        "reason_note": "second",
    }
    res2 = await client.post("/api/v1/recalls/", json=payload2, headers=auth_headers)
    assert res2.status_code == 201, res2.text
    second = res2.json()["data"]
    assert second["id"] == first["id"]  # same row
    assert second["due_month"] == "2026-09-01"
    assert second["priority"] == "high"

    # List shows exactly one row.
    list_res = await client.get(
        f"/api/v1/recalls/?patient_id={test_patient.id}&page_size=10",
        headers=auth_headers,
    )
    assert list_res.status_code == 200
    body = list_res.json()
    assert body["total"] == 1
    assert body["data"][0]["patient"]["first_name"] == "Test"


@pytest.mark.asyncio
async def test_log_attempt_auto_transitions_status(
    client: AsyncClient, auth_headers: dict, test_patient: Patient
):
    # Seed a recall.
    create = await client.post(
        "/api/v1/recalls/",
        json={
            "patient_id": str(test_patient.id),
            "due_month": "2026-07-01",
            "reason": "checkup",
        },
        headers=auth_headers,
    )
    rid = create.json()["data"]["id"]

    res = await client.post(
        f"/api/v1/recalls/{rid}/attempts",
        json={"channel": "phone", "outcome": "no_answer"},
        headers=auth_headers,
    )
    assert res.status_code == 201, res.text

    detail = (await client.get(f"/api/v1/recalls/{rid}", headers=auth_headers)).json()["data"]
    assert detail["status"] == "contacted_no_answer"
    assert detail["contact_attempt_count"] == 1
    assert len(detail["attempts"]) == 1


@pytest.mark.asyncio
async def test_snooze_bumps_due_month_forward(
    client: AsyncClient, auth_headers: dict, test_patient: Patient
):
    create = await client.post(
        "/api/v1/recalls/",
        json={
            "patient_id": str(test_patient.id),
            "due_month": "2026-06-01",
            "reason": "hygiene",
        },
        headers=auth_headers,
    )
    rid = create.json()["data"]["id"]

    res = await client.post(
        f"/api/v1/recalls/{rid}/snooze",
        json={"months": 4},
        headers=auth_headers,
    )
    assert res.status_code == 200, res.text
    assert res.json()["data"]["due_month"] == "2026-10-01"


@pytest.mark.asyncio
async def test_settings_lazy_create_and_update(
    client: AsyncClient, auth_headers: dict, test_clinic: Clinic
):
    res = await client.get("/api/v1/recalls/settings", headers=auth_headers)
    assert res.status_code == 200
    settings = res.json()["data"]
    assert settings["clinic_id"] == str(test_clinic.id)
    assert settings["reason_intervals"]["hygiene"] == 6
    assert settings["category_to_reason"]["preventivo"] == "hygiene"
    assert settings["auto_suggest_on_treatment_completed"] is True

    update = await client.put(
        "/api/v1/recalls/settings",
        json={
            "reason_intervals": {**settings["reason_intervals"], "hygiene": 4},
            "auto_suggest_on_treatment_completed": False,
        },
        headers=auth_headers,
    )
    assert update.status_code == 200, update.text
    updated = update.json()["data"]
    assert updated["reason_intervals"]["hygiene"] == 4
    assert updated["auto_suggest_on_treatment_completed"] is False


@pytest.mark.asyncio
async def test_dashboard_stats_endpoint(
    client: AsyncClient, auth_headers: dict, test_patient: Patient
):
    # Seed a recall so the counters are non-zero where relevant.
    await client.post(
        "/api/v1/recalls/",
        json={
            "patient_id": str(test_patient.id),
            "due_month": "1900-01-01",
            "reason": "checkup",
        },
        headers=auth_headers,
    )
    res = await client.get("/api/v1/recalls/stats/dashboard", headers=auth_headers)
    assert res.status_code == 200
    stats = res.json()["data"]
    assert stats["overdue"] >= 1
    assert isinstance(stats["conversion_rate"], float)


@pytest.mark.asyncio
async def test_do_not_contact_excluded_from_active_list(
    client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
    test_patient: Patient,
):
    await client.post(
        "/api/v1/recalls/",
        json={
            "patient_id": str(test_patient.id),
            "due_month": "2026-08-01",
            "reason": "hygiene",
        },
        headers=auth_headers,
    )
    test_patient.do_not_contact = True
    await db_session.commit()

    res = await client.get("/api/v1/recalls/?page_size=10", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["total"] == 0

    # Opting in surfaces the row again.
    res2 = await client.get(
        "/api/v1/recalls/?include_do_not_contact=true&page_size=10",
        headers=auth_headers,
    )
    assert res2.status_code == 200
    assert res2.json()["total"] == 1


@pytest.mark.asyncio
async def test_suggestion_returns_null_when_no_mapping(
    client: AsyncClient, auth_headers: dict, test_patient: Patient
):
    res = await client.get(
        f"/api/v1/recalls/suggestions/next?patient_id={test_patient.id}",
        headers=auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["data"] is None


@pytest.mark.asyncio
async def test_suggestion_uses_category_map(
    client: AsyncClient, auth_headers: dict, test_patient: Patient
):
    res = await client.get(
        f"/api/v1/recalls/suggestions/next?patient_id={test_patient.id}"
        f"&treatment_category_key=preventivo",
        headers=auth_headers,
    )
    assert res.status_code == 200
    suggestion = res.json()["data"]
    assert suggestion is not None
    assert suggestion["reason"] == "hygiene"
    assert suggestion["interval_months"] == 6
    assert suggestion["matched_setting"] is True
