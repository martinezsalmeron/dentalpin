"""Service layer for agents, audit and approval queue."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.agents.context import AgentContext
from app.core.agents.models import (
    Agent,
    AgentApprovalQueue,
    AgentAuditLog,
    AgentSession,
)


class AgentService:
    """CRUD for agent definitions and sessions."""

    @staticmethod
    async def list_agents(db: AsyncSession, clinic_id: UUID) -> list[Agent]:
        result = await db.execute(
            select(Agent).where(Agent.clinic_id == clinic_id).order_by(Agent.created_at)
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_agent(
        db: AsyncSession,
        clinic_id: UUID,
        *,
        name: str,
        type: str,
        mode: str,
        config: dict[str, Any] | None = None,
    ) -> Agent:
        agent = Agent(
            clinic_id=clinic_id,
            name=name,
            type=type,
            mode=mode,
            config=config or {},
        )
        db.add(agent)
        await db.flush()
        return agent

    @staticmethod
    async def start_session(
        db: AsyncSession,
        *,
        agent_id: UUID,
        clinic_id: UUID,
        supervisor_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AgentSession:
        session = AgentSession(
            agent_id=agent_id,
            clinic_id=clinic_id,
            supervisor_id=supervisor_id,
            session_metadata=metadata or {},
        )
        db.add(session)
        await db.flush()
        return session

    @staticmethod
    async def list_sessions(
        db: AsyncSession, clinic_id: UUID, agent_id: UUID
    ) -> list[AgentSession]:
        result = await db.execute(
            select(AgentSession)
            .where(AgentSession.clinic_id == clinic_id, AgentSession.agent_id == agent_id)
            .order_by(AgentSession.created_at.desc())
        )
        return list(result.scalars().all())


class AuditService:
    """Append-only audit log. Every tool attempt writes one row."""

    @staticmethod
    async def record(
        ctx: AgentContext,
        tool_name: str,
        arguments: dict[str, Any],
        *,
        result: dict[str, Any] | None = None,
        error: str | None = None,
        status: str,
        execution_time_ms: int,
    ) -> AgentAuditLog:
        log = AgentAuditLog(
            agent_id=ctx.agent_id,
            session_id=ctx.session_id,
            clinic_id=ctx.clinic_id,
            supervisor_id=ctx.supervisor_id,
            tool_name=tool_name,
            tool_arguments=arguments,
            result=result,
            error=error,
            status=status,
            execution_time_ms=execution_time_ms,
        )
        ctx.db.add(log)
        await ctx.db.flush()
        return log

    @staticmethod
    async def list_for_clinic(
        db: AsyncSession,
        clinic_id: UUID,
        *,
        agent_id: UUID | None = None,
        limit: int = 100,
    ) -> list[AgentAuditLog]:
        query = select(AgentAuditLog).where(AgentAuditLog.clinic_id == clinic_id)
        if agent_id is not None:
            query = query.where(AgentAuditLog.agent_id == agent_id)
        query = query.order_by(AgentAuditLog.created_at.desc()).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())


class ApprovalService:
    """Human-in-the-loop approval queue for supervised agents."""

    @staticmethod
    async def request_approval(
        ctx: AgentContext,
        tool_name: str,
        arguments: dict[str, Any],
        *,
        reason: str | None = None,
    ) -> AgentApprovalQueue:
        request = AgentApprovalQueue(
            id=uuid4(),
            agent_id=ctx.agent_id,
            session_id=ctx.session_id,
            clinic_id=ctx.clinic_id,
            tool_name=tool_name,
            arguments=arguments,
            reason=reason,
            status="pending",
        )
        ctx.db.add(request)
        await ctx.db.flush()
        return request

    @staticmethod
    async def list_pending(
        db: AsyncSession, clinic_id: UUID, *, status: str = "pending"
    ) -> list[AgentApprovalQueue]:
        result = await db.execute(
            select(AgentApprovalQueue)
            .where(
                AgentApprovalQueue.clinic_id == clinic_id,
                AgentApprovalQueue.status == status,
            )
            .order_by(AgentApprovalQueue.created_at.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def _decide(
        db: AsyncSession,
        clinic_id: UUID,
        request_id: UUID,
        *,
        reviewer_id: UUID,
        status: str,
        notes: str | None,
    ) -> AgentApprovalQueue | None:
        result = await db.execute(
            select(AgentApprovalQueue).where(
                AgentApprovalQueue.id == request_id,
                AgentApprovalQueue.clinic_id == clinic_id,
            )
        )
        request = result.scalar_one_or_none()
        if request is None or request.status != "pending":
            return None
        request.status = status
        request.reviewed_by = reviewer_id
        request.reviewed_at = datetime.now(UTC)
        request.review_notes = notes
        await db.flush()
        return request

    @staticmethod
    async def approve(
        db: AsyncSession,
        clinic_id: UUID,
        request_id: UUID,
        *,
        reviewer_id: UUID,
        notes: str | None = None,
    ) -> AgentApprovalQueue | None:
        return await ApprovalService._decide(
            db,
            clinic_id,
            request_id,
            reviewer_id=reviewer_id,
            status="approved",
            notes=notes,
        )

    @staticmethod
    async def reject(
        db: AsyncSession,
        clinic_id: UUID,
        request_id: UUID,
        *,
        reviewer_id: UUID,
        notes: str | None = None,
    ) -> AgentApprovalQueue | None:
        return await ApprovalService._decide(
            db,
            clinic_id,
            request_id,
            reviewer_id=reviewer_id,
            status="rejected",
            notes=notes,
        )
