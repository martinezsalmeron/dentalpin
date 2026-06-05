"""(De)serialize neutral message blocks ↔ JSON for ``copilot_messages``."""

from __future__ import annotations

from typing import Any

from app.core.llm.base import (
    ContentBlock,
    ProviderMessage,
    Role,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
)


def block_to_dict(block: ContentBlock) -> dict[str, Any]:
    if isinstance(block, TextBlock):
        return {"type": "text", "text": block.text}
    if isinstance(block, ToolUseBlock):
        return {"type": "tool_use", "id": block.id, "name": block.name, "input": block.input}
    if isinstance(block, ToolResultBlock):
        return {
            "type": "tool_result",
            "tool_call_id": block.tool_call_id,
            "content": block.content,
            "is_error": block.is_error,
        }
    raise TypeError(f"unknown block: {block!r}")


def dict_to_block(data: dict[str, Any]) -> ContentBlock:
    kind = data.get("type")
    if kind == "text":
        return TextBlock(data["text"])
    if kind == "tool_use":
        return ToolUseBlock(data["id"], data["name"], data.get("input", {}))
    if kind == "tool_result":
        return ToolResultBlock(
            data["tool_call_id"], data.get("content"), data.get("is_error", False)
        )
    raise ValueError(f"unknown block type: {kind!r}")


def content_to_json(blocks: list[ContentBlock]) -> list[dict]:
    return [block_to_dict(b) for b in blocks]


def message_from_row(role: str, content: list[dict]) -> ProviderMessage:
    return ProviderMessage(role=Role(role), content=[dict_to_block(b) for b in content])
