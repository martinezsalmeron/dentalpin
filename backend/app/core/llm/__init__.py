"""Vendor-agnostic LLM provider layer.

Public surface:

* :class:`Provider` — the streaming protocol the orchestrator depends on.
* neutral message/event types (:class:`ProviderMessage`, :class:`TextBlock`,
  :class:`ToolUseBlock`, :class:`ToolResultBlock`, :class:`TextDelta`,
  :class:`ToolUse`, :class:`Usage`, :class:`Done`, :class:`Role`).
* :func:`get_provider` — resolve a provider by name (v1: ``"openai"``).
"""

from app.core.llm.base import (
    ContentBlock,
    Done,
    LLMConfigError,
    LLMError,
    Provider,
    ProviderEvent,
    ProviderMessage,
    Role,
    TextBlock,
    TextDelta,
    ToolResultBlock,
    ToolUse,
    ToolUseBlock,
    Usage,
)
from app.core.llm.factory import get_provider

__all__ = [
    "ContentBlock",
    "Done",
    "LLMConfigError",
    "LLMError",
    "Provider",
    "ProviderEvent",
    "ProviderMessage",
    "Role",
    "TextBlock",
    "TextDelta",
    "ToolResultBlock",
    "ToolUse",
    "ToolUseBlock",
    "Usage",
    "get_provider",
]
