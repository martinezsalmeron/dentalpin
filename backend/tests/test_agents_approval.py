"""Tests for the approval queue flow (supervised mode)."""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from app.core.agents import AgentContext, AgentMode, Tool, ToolCategory, tool_registry
from app.core.agents.guardrails import reset_counters
from app.core.agents.models import Agent, AgentApprovalQueue, AgentSession
from app.core.agents.service import ApprovalService
from app.core.auth.models import ClinicMembership
from app.core.plugins.base import BaseModule


class _Args(BaseModel):
    target: str


async def _write(ctx, params):
    return {"wrote": params.target}


class _ApprovalsFixture(BaseModule):
    manifest = {
        "name": "approvals_fixture",
        "version": "0.0.1",
        "summary": "x",
        "category": "official",
        "installable": True,
        "auto_install": True,
        "removable": True,
    }

    def get_models(self):
        return []

    def get_router(self) -> APIRouter:
        return APIRouter()

    def get_tools(self):
        return [
            Tool(
                name="write_thing",
                description="writes",
                parameters=_Args,
                handler=_write,
                permissions=[],
                category=ToolCategory.WRITE,
            )
        ]


@pytest.fixture(autouse=True)
def _module_fixture():
    tool_registry.register_from(_ApprovalsFixture())
    reset_counters()
    yield
    tool_registry.unregister_module("approvals_fixture")
    reset_counters()


async def _setup(db_session, clinic):
    agent = Agent(clinic_id=clinic.id, name="a", type="fixture", mode="supervised", config={})
    db_session.add(agent)
    await db_session.flush()
    session = AgentSession(agent_id=agent.id, clinic_id=clinic.id)
    db_session.add(session)
    await db_session.flush()
    return agent, session


async def _clinic_admin_id(db_session, clinic):
    """Return any user_id with membership in the test clinic (FK-safe reviewer)."""
    result = await db_session.execute(
        select(ClinicMembership.user_id).where(ClinicMembership.clinic_id == clinic.id)
    )
    return result.scalars().first()


@pytest.mark.asyncio
async def test_supervised_write_enqueues_approval(db_session, test_clinic):
    agent, session = await _setup(db_session, test_clinic)
    ctx = AgentContext(
        agent_id=agent.id,
        session_id=session.id,
        clinic_id=test_clinic.id,
        mode=AgentMode.SUPERVISED,
        permissions=["*"],
        tools=tool_registry,
        db=db_session,
    )

    result = await tool_registry.call(ctx, "approvals_fixture.write_thing", {"target": "room"})

    assert result.ok is False
    assert result.error == "pending approval"
    assert "approval_request_id" in (result.data or {})

    pending = await ApprovalService.list_pending(db_session, test_clinic.id)
    assert len(pending) == 1
    assert pending[0].tool_name == "approvals_fixture.write_thing"
    assert pending[0].arguments == {"target": "room"}


@pytest.mark.asyncio
async def test_approve_marks_request_approved(db_session, test_clinic):
    agent, session = await _setup(db_session, test_clinic)
    req = AgentApprovalQueue(
        agent_id=agent.id,
        session_id=session.id,
        clinic_id=test_clinic.id,
        tool_name="x.y",
        arguments={},
        status="pending",
    )
    db_session.add(req)
    await db_session.flush()

    reviewer_id = await _clinic_admin_id(db_session, test_clinic)
    approved = await ApprovalService.approve(
        db_session,
        test_clinic.id,
        req.id,
        reviewer_id=reviewer_id,
        notes="looks good",
    )
    assert approved is not None
    assert approved.status == "approved"
    assert approved.reviewed_by == reviewer_id
    assert approved.review_notes == "looks good"


@pytest.mark.asyncio
async def test_reject_is_idempotent_against_double_decision(db_session, test_clinic):
    agent, session = await _setup(db_session, test_clinic)
    req = AgentApprovalQueue(
        agent_id=agent.id,
        session_id=session.id,
        clinic_id=test_clinic.id,
        tool_name="x.y",
        arguments={},
        status="pending",
    )
    db_session.add(req)
    await db_session.flush()

    reviewer_id = await _clinic_admin_id(db_session, test_clinic)
    await ApprovalService.reject(db_session, test_clinic.id, req.id, reviewer_id=reviewer_id)
    # Second decision on an already-decided request returns None.
    second = await ApprovalService.approve(
        db_session, test_clinic.id, req.id, reviewer_id=reviewer_id
    )
    assert second is None


@pytest.mark.asyncio
async def test_cross_clinic_access_returns_none(db_session, test_clinic):
    agent, session = await _setup(db_session, test_clinic)
    req = AgentApprovalQueue(
        agent_id=agent.id,
        session_id=session.id,
        clinic_id=test_clinic.id,
        tool_name="x.y",
        arguments={},
        status="pending",
    )
    db_session.add(req)
    await db_session.flush()

    other_clinic_id = uuid4()
    reviewer_id = await _clinic_admin_id(db_session, test_clinic)
    result = await ApprovalService.approve(
        db_session, other_clinic_id, req.id, reviewer_id=reviewer_id
    )
    assert result is None
