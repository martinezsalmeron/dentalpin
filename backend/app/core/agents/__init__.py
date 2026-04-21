"""AI Agent integration infrastructure.

Provides the contract every module uses to expose callable actions
(tools) and autonomous/supervised agents to the rest of the system.

Public surface:

* :data:`tool_registry` — global registry collecting tools from every
  loaded module. All tool invocations MUST flow through
  ``tool_registry.call()`` so that permissions, guardrails and audit
  logging are enforced at a single chokepoint.
* :class:`BaseAgent` — abstract base class modules subclass to build
  an agent. Modules register their agents via
  ``BaseModule.get_agents()``.
* :class:`AgentContext` — carries user / clinic / permissions / tools /
  memory into every tool invocation and agent run.
* :class:`Tool`, :class:`ToolCategory` — the dataclass every module
  returns from ``get_tools()``.
"""

from app.core.agents.base import BaseAgent
from app.core.agents.context import AgentContext, AgentMode, AgentResult
from app.core.agents.tools.registry import ToolRegistry, tool_registry
from app.core.agents.tools.tool import Tool, ToolCategory, ToolResult

__all__ = [
    "AgentContext",
    "AgentMode",
    "AgentResult",
    "BaseAgent",
    "Tool",
    "ToolCategory",
    "ToolRegistry",
    "ToolResult",
    "tool_registry",
]
