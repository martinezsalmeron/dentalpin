"""Agent execution context and result types."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any
from uuid import UUID

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.core.agents.memory import AgentMemory
    from app.core.agents.tools.registry import ToolRegistry


class AgentMode(StrEnum):
    """How an agent's actions are gated.

    ``AUTONOMOUS`` agents execute tool calls immediately, subject only
    to guardrails and RBAC. ``SUPERVISED`` agents queue every write
    action for human approval before it takes effect.
    """

    AUTONOMOUS = "autonomous"
    SUPERVISED = "supervised"


@dataclass
class AgentContext:
    """State passed into every tool handler and agent run.

    The context is the single source of truth for *who* is acting and
    *where* they are acting. Tool handlers MUST filter by
    ``clinic_id`` the same way regular router endpoints do.
    """

    agent_id: UUID
    session_id: UUID
    clinic_id: UUID
    mode: AgentMode
    permissions: list[str]
    tools: ToolRegistry
    db: AsyncSession
    memory: AgentMemory | None = None
    supervisor_id: UUID | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    """Outcome of a single agent run."""

    ok: bool
    summary: str = ""
    data: dict[str, Any] = field(default_factory=dict)
