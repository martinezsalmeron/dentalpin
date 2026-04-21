"""Tool dataclass and supporting types."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

if TYPE_CHECKING:
    from app.core.agents.context import AgentContext


class ToolCategory(StrEnum):
    """Coarse classification that drives default guardrail policy.

    ``READ`` tools never mutate state. ``WRITE`` tools mutate but are
    recoverable. ``DESTRUCTIVE`` tools delete data or trigger external
    side-effects that cannot be undone; guardrails default to requiring
    human approval for them.
    """

    READ = "read"
    WRITE = "write"
    DESTRUCTIVE = "destructive"


ToolHandler = Callable[["AgentContext", BaseModel], Awaitable[Any]]


@dataclass(frozen=True)
class Tool:
    """Callable action a module exposes to AI agents.

    The registry namespaces names at registration time: a tool named
    ``create_appointment`` registered by the ``agenda`` module becomes
    ``agenda.create_appointment`` in the global registry.
    """

    name: str
    description: str
    parameters: type[BaseModel]
    handler: ToolHandler
    permissions: list[str] = field(default_factory=list)
    category: ToolCategory = ToolCategory.READ


@dataclass
class ToolResult:
    """Wrapper around a tool invocation's return value."""

    ok: bool
    data: Any = None
    error: str | None = None
    execution_time_ms: int = 0
