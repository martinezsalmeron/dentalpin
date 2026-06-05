"""Vendor-neutral LLM types and the ``Provider`` protocol.

The orchestrator (``app/core/agents/orchestrator.py``) works exclusively
on these neutral types. Each provider implementation adapts to and from
its vendor wire format, so adding a new vendor (Anthropic, Ollama) is a
single new file under this package — nothing above ``app/core/llm/``
changes. See ``docs/technical/copilot-agentic-architecture.md`` §2.1.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable


class LLMError(Exception):
    """Base error for the LLM layer."""


class LLMConfigError(LLMError):
    """Raised when a provider is misconfigured (unknown name, missing key)."""


class Role(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


# --- Neutral content blocks ---------------------------------------------


@dataclass
class TextBlock:
    """A chunk of natural-language text in a message."""

    text: str


@dataclass
class ToolUseBlock:
    """A model's request to invoke a tool (lives on an assistant message)."""

    id: str
    name: str
    input: dict[str, Any]


@dataclass
class ToolResultBlock:
    """The outcome of a tool call (lives on a ``tool`` message)."""

    tool_call_id: str
    content: Any
    is_error: bool = False


ContentBlock = TextBlock | ToolUseBlock | ToolResultBlock


@dataclass
class ProviderMessage:
    """One vendor-agnostic conversation turn.

    A ``user`` turn carries text blocks; an ``assistant`` turn may carry
    text and/or tool-use blocks; a ``tool`` turn carries tool-result
    blocks. Providers serialize this to their own shape (Anthropic
    content blocks vs OpenAI ``tool_calls`` + ``role:"tool"`` messages).
    """

    role: Role
    content: list[ContentBlock] = field(default_factory=list)


# --- Neutral streaming events -------------------------------------------


@dataclass
class TextDelta:
    """An incremental piece of assistant text."""

    text: str


@dataclass
class ToolUse:
    """A fully-assembled tool call emitted by the provider."""

    id: str
    name: str
    input: dict[str, Any]


@dataclass
class Usage:
    """Token accounting for one provider completion."""

    input_tokens: int
    output_tokens: int


@dataclass
class Done:
    """Terminal event for one provider completion."""

    stop_reason: str


ProviderEvent = TextDelta | ToolUse | Usage | Done


@runtime_checkable
class Provider(Protocol):
    """A streaming chat-completions backend.

    Implementations are async generators: calling ``complete(...)``
    returns an ``AsyncIterator[ProviderEvent]`` synchronously (no await).
    """

    def complete(
        self,
        *,
        system: str,
        messages: list[ProviderMessage],
        tools: list[dict],
        model: str,
        max_tokens: int,
    ) -> AsyncIterator[ProviderEvent]: ...
