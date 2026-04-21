"""Agent memory protocol and a minimal in-memory implementation.

Real production backends (Redis for short-term, Postgres for long-term)
land with the first concrete agent that needs them. The Protocol is
defined now so agent code written against it is stable.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID


@dataclass
class MemoryMessage:
    role: str
    content: str


class AgentMemory(Protocol):
    """Persistent or ephemeral per-session memory for an agent."""

    async def add_message(self, session_id: UUID, role: str, content: str) -> None: ...

    async def get_history(self, session_id: UUID, limit: int = 50) -> list[MemoryMessage]: ...

    async def set_context(self, session_id: UUID, key: str, value: Any) -> None: ...

    async def get_context(self, session_id: UUID, key: str) -> Any | None: ...


class InMemoryMemory:
    """Process-local memory. Loses state on restart; tests + dev only."""

    def __init__(self) -> None:
        self._messages: dict[UUID, list[MemoryMessage]] = defaultdict(list)
        self._context: dict[UUID, dict[str, Any]] = defaultdict(dict)

    async def add_message(self, session_id: UUID, role: str, content: str) -> None:
        self._messages[session_id].append(MemoryMessage(role=role, content=content))

    async def get_history(self, session_id: UUID, limit: int = 50) -> list[MemoryMessage]:
        return self._messages[session_id][-limit:]

    async def set_context(self, session_id: UUID, key: str, value: Any) -> None:
        self._context[session_id][key] = value

    async def get_context(self, session_id: UUID, key: str) -> Any | None:
        return self._context[session_id].get(key)
