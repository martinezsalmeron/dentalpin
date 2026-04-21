"""Pydantic → JSON Schema helper for LLM function-calling APIs."""

from __future__ import annotations

from pydantic import BaseModel

from app.core.agents.tools.tool import Tool


def pydantic_to_json_schema(model_cls: type[BaseModel]) -> dict:
    """Return a JSON Schema dict for a Pydantic V2 model.

    Both Anthropic's ``input_schema`` field and OpenAI's ``parameters``
    field accept this format verbatim.
    """
    return model_cls.model_json_schema()


def tool_to_anthropic_schema(tool: Tool, qualified_name: str) -> dict:
    """Serialize a tool in the shape Anthropic's tool-use API expects."""
    return {
        "name": qualified_name,
        "description": tool.description,
        "input_schema": pydantic_to_json_schema(tool.parameters),
    }


def tool_to_openai_schema(tool: Tool, qualified_name: str) -> dict:
    """Serialize a tool in the shape OpenAI's function-calling API expects."""
    return {
        "type": "function",
        "function": {
            "name": qualified_name,
            "description": tool.description,
            "parameters": pydantic_to_json_schema(tool.parameters),
        },
    }
