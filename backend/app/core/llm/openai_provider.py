"""OpenAI implementation of the neutral :class:`Provider` protocol.

v1 ships this provider only. It maps the neutral message/event types in
``base.py`` to and from the OpenAI Chat Completions streaming API.

Tool calling is forced single (``parallel_tool_calls=False``) so the
orchestrator can apply its one-tool-per-turn inline-confirmation model
without juggling partially-resolved tool batches.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from app.core.llm.base import (
    Done,
    LLMConfigError,
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


class OpenAIProvider:
    """Streams completions from OpenAI, speaking neutral types."""

    def __init__(self, *, api_key: str) -> None:
        if not api_key:
            raise LLMConfigError("OpenAI provider requires OPENAI_API_KEY")
        # Imported lazily so the dependency is only needed when the
        # provider is actually instantiated (keeps test/import light).
        from openai import AsyncOpenAI

        self._client = AsyncOpenAI(api_key=api_key)

    async def complete(
        self,
        *,
        system: str,
        messages: list[ProviderMessage],
        tools: list[dict],
        model: str,
        max_tokens: int,
    ) -> AsyncIterator[ProviderEvent]:
        wire_messages = _to_openai_messages(system, messages)
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": wire_messages,
            "max_tokens": max_tokens,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        if tools:
            kwargs["tools"] = [_sanitize_tool_schema(t) for t in tools]
            kwargs["parallel_tool_calls"] = False

        # index -> {"id": str, "name": str, "args": str}
        pending: dict[int, dict[str, str]] = {}
        stop_reason = "stop"

        stream = await self._client.chat.completions.create(**kwargs)
        async for chunk in stream:
            # The usage-only final chunk carries no choices.
            if chunk.usage is not None:
                yield Usage(
                    input_tokens=chunk.usage.prompt_tokens,
                    output_tokens=chunk.usage.completion_tokens,
                )
            if not chunk.choices:
                continue

            choice = chunk.choices[0]
            delta = choice.delta

            if delta is not None and delta.content:
                yield TextDelta(text=delta.content)

            if delta is not None and delta.tool_calls:
                for tc in delta.tool_calls:
                    slot = pending.setdefault(tc.index, {"id": "", "name": "", "args": ""})
                    if tc.id:
                        slot["id"] = tc.id
                    if tc.function is not None:
                        if tc.function.name:
                            slot["name"] = tc.function.name
                        if tc.function.arguments:
                            slot["args"] += tc.function.arguments

            if choice.finish_reason:
                stop_reason = choice.finish_reason

        for slot in pending.values():
            yield ToolUse(
                id=slot["id"],
                name=_from_openai_name(slot["name"]),
                input=_parse_args(slot["args"]),
            )

        yield Done(stop_reason=stop_reason)


# OpenAI restricts function names to ``^[a-zA-Z0-9_-]+$``, but our tool
# registry namespaces with a dot (``patients.search_patients``). Tool /
# module names are snake_case with no hyphens, so ``.`` <-> ``-`` is a
# lossless bijection confined to this provider.
def _to_openai_name(qualified: str) -> str:
    return qualified.replace(".", "-")


def _from_openai_name(safe: str) -> str:
    return safe.replace("-", ".")


def _sanitize_tool_schema(tool: dict[str, Any]) -> dict[str, Any]:
    fn = tool.get("function", {})
    return {**tool, "function": {**fn, "name": _to_openai_name(fn["name"])}}


def _parse_args(raw: str) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _to_openai_messages(system: str, messages: list[ProviderMessage]) -> list[dict[str, Any]]:
    """Flatten neutral messages into OpenAI's wire shape.

    One neutral ``tool`` message with N result blocks expands into N
    OpenAI ``role:"tool"`` messages (one per ``tool_call_id``).
    """
    out: list[dict[str, Any]] = []
    if system:
        out.append({"role": "system", "content": system})

    for msg in messages:
        if msg.role is Role.USER:
            out.append({"role": "user", "content": _join_text(msg)})

        elif msg.role is Role.ASSISTANT:
            text = _join_text(msg)
            tool_calls = [
                {
                    "id": block.id,
                    "type": "function",
                    "function": {
                        "name": _to_openai_name(block.name),
                        "arguments": json.dumps(block.input),
                    },
                }
                for block in msg.content
                if isinstance(block, ToolUseBlock)
            ]
            wire: dict[str, Any] = {"role": "assistant", "content": text or None}
            if tool_calls:
                wire["tool_calls"] = tool_calls
            out.append(wire)

        elif msg.role is Role.TOOL:
            for block in msg.content:
                if isinstance(block, ToolResultBlock):
                    out.append(
                        {
                            "role": "tool",
                            "tool_call_id": block.tool_call_id,
                            "content": _stringify(block.content),
                        }
                    )

    return out


def _join_text(msg: ProviderMessage) -> str:
    return "".join(b.text for b in msg.content if isinstance(b, TextBlock))


def _stringify(content: Any) -> str:
    if isinstance(content, str):
        return content
    return json.dumps(content, ensure_ascii=False, default=str)
