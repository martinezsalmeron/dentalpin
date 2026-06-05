"""Layer B: agent tools for patients + agenda.

Exercises the real tools through the registry chokepoint with a live DB,
covering RBAC parity and multi-tenancy isolation (the two invariants that
make the agent safe).
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.agents.context import AgentContext, AgentMode
from app.core.agents.models import Agent, AgentSession
from app.core.agents.tools.registry import tool_registry
from app.modules.patients.service import PatientService


async def _agent_session(db: AsyncSession, clinic_id) -> tuple:
    agent = Agent(clinic_id=clinic_id, name="copilot", type="copilot", mode="autonomous", config={})
    db.add(agent)
    await db.flush()
    session = AgentSession(agent_id=agent.id, clinic_id=clinic_id)
    db.add(session)
    await db.flush()
    return agent, session


async def _ctx(db: AsyncSession, clinic_id, permissions: list[str]) -> AgentContext:
    agent, session = await _agent_session(db, clinic_id)
    return AgentContext(
        agent_id=agent.id,
        session_id=session.id,
        clinic_id=clinic_id,
        mode=AgentMode.AUTONOMOUS,
        permissions=permissions,
        tools=tool_registry,
        db=db,
    )


def test_tools_are_registered() -> None:
    names = tool_registry.list()
    for expected in (
        "patients.search_patients",
        "patients.get_patient",
        "patients.create_patient",
        "agenda.get_day_overview",
        "agenda.book_appointment",
        "agenda.cancel_appointment",
    ):
        assert expected in names


@pytest.mark.asyncio
async def test_create_then_search_patient(db_session, test_clinic) -> None:
    ctx = await _ctx(db_session, test_clinic.id, ["patients.read", "patients.write"])

    created = await tool_registry.call(
        ctx, "patients.create_patient", {"first_name": "María", "last_name": "González"}
    )
    assert created.ok
    assert created.data["full_name"] == "María González"

    found = await tool_registry.call(ctx, "patients.search_patients", {"query": "María"})
    assert found.ok
    assert found.data["total"] >= 1
    assert any(p["full_name"] == "María González" for p in found.data["patients"])


@pytest.mark.asyncio
async def test_create_patient_denied_without_write(db_session, test_clinic) -> None:
    ctx = await _ctx(db_session, test_clinic.id, ["patients.read"])  # read only
    res = await tool_registry.call(
        ctx, "patients.create_patient", {"first_name": "Ana", "last_name": "Ruiz"}
    )
    assert res.ok is False
    assert "permission denied" in (res.error or "")


@pytest.mark.asyncio
async def test_search_is_clinic_scoped(db_session, test_clinic) -> None:
    from app.core.auth.models import Clinic

    # Patient belongs to a *different* clinic.
    other = Clinic(id=uuid4(), name="Other Clinic", tax_id="X99999999", settings={})
    db_session.add(other)
    await db_session.flush()
    await PatientService.create_patient(
        db_session, other.id, {"first_name": "Bruno", "last_name": "Otero"}
    )
    await db_session.flush()

    ctx = await _ctx(db_session, test_clinic.id, ["patients.read"])
    res = await tool_registry.call(ctx, "patients.search_patients", {"query": "Bruno"})
    assert res.ok
    assert all(p["full_name"] != "Bruno Otero" for p in res.data["patients"])


@pytest.mark.asyncio
async def test_day_overview_empty(db_session, test_clinic) -> None:
    ctx = await _ctx(db_session, test_clinic.id, ["agenda.appointments.read"])
    res = await tool_registry.call(ctx, "agenda.get_day_overview", {"date": "2030-01-01"})
    assert res.ok
    assert res.data["total"] == 0


def test_p0_tools_registered() -> None:
    names = tool_registry.list()
    for expected in (
        "schedules.get_availability",
        "patient_timeline.get_patient_timeline",
        "agenda.get_appointment",
        "agenda.list_cabinets",
    ):
        assert expected in names


@pytest.mark.asyncio
async def test_list_cabinets(db_session, test_clinic) -> None:
    ctx = await _ctx(db_session, test_clinic.id, ["agenda.cabinets.read"])
    res = await tool_registry.call(ctx, "agenda.list_cabinets", {})
    assert res.ok
    assert any(c["name"] == "Gabinete 1" for c in res.data["cabinets"])


@pytest.mark.asyncio
async def test_get_availability_runs(db_session, test_clinic) -> None:
    ctx = await _ctx(db_session, test_clinic.id, ["schedules.availability.read"])
    res = await tool_registry.call(ctx, "schedules.get_availability", {"date": "2030-01-07"})
    assert res.ok
    assert "open_windows" in res.data


@pytest.mark.asyncio
async def test_patient_timeline_empty(db_session, test_clinic) -> None:
    from uuid import uuid4

    ctx = await _ctx(db_session, test_clinic.id, ["patient_timeline.read"])
    res = await tool_registry.call(
        ctx, "patient_timeline.get_patient_timeline", {"patient_id": str(uuid4())}
    )
    assert res.ok
    assert res.data["total"] == 0


@pytest.mark.asyncio
async def test_book_appointment_denied_without_write(db_session, test_clinic) -> None:
    ctx = await _ctx(db_session, test_clinic.id, ["agenda.appointments.read"])  # no write
    res = await tool_registry.call(
        ctx,
        "agenda.book_appointment",
        {
            "patient_id": str(uuid4()),
            "professional_id": str(uuid4()),
            "start_time": "2030-01-01T10:00:00+00:00",
            "end_time": "2030-01-01T10:30:00+00:00",
        },
    )
    assert res.ok is False
    assert "permission denied" in (res.error or "")
