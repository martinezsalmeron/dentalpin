"""Provider resolution.

v1 resolves ``"openai"`` only. Anthropic / Ollama slot in here later
with no change to callers — the orchestrator already speaks neutral
types (``base.py``).
"""

from __future__ import annotations

from app.config import settings
from app.core.llm.base import LLMConfigError, Provider

SUPPORTED_PROVIDERS = ("openai",)


def get_provider(name: str, *, api_key: str | None = None) -> Provider:
    """Return a configured :class:`Provider` for ``name``.

    Raises :class:`LLMConfigError` for unsupported names so a clinic can
    never select a provider this deployment cannot serve.
    """
    if name == "openai":
        from app.core.llm.openai_provider import OpenAIProvider

        return OpenAIProvider(api_key=api_key or settings.OPENAI_API_KEY)

    raise LLMConfigError(
        f"Unsupported LLM provider: {name!r} (supported: {', '.join(SUPPORTED_PROVIDERS)})"
    )
