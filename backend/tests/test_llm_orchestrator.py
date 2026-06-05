"""Layer A core-engine tests: provider abstraction, redaction, orchestrator.

DB-free: the orchestrator only touches three methods on ``ctx.tools``
(``get`` / ``schemas_for`` / ``call``), so a duck-typed fake registry and
a scripted fake provider exercise the whole loop without Postgres.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
from pydantic import BaseModel

from app.core.agents.context import AgentContext, AgentMode
from app.core.agents.orchestrator import (
    BudgetExceeded,
    ConfirmationRequired,
    Final,
    Token,
    ToolCallFinished,
    ToolCallStarted,
    TurnUsage,
    run_turn,
)
from app.core.agents.redaction import Redactor
from app.core.agents.tools.schema import tool_to_openai_schema
from app.core.agents.tools.tool import Tool, ToolCategory, ToolResult
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
    Usage,
)
from app.core.llm.factory import get_provider


class _Args(BaseModel):
    q: str = ""


class _FakeRegistry:
    """Implements the ToolRegistry surface the orchestrator uses."""

    def __init__(self, tools: dict[str, Tool]) -> None:
        self._tools = tools
        self.calls: list[tuple[str, dict]] = []

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def schemas_for(self, names: list[str], dialect: str = "openai") -> list[dict]:
        return [tool_to_openai_schema(self._tools[n], n) for n in names]

    async def call(self, ctx, name: str, args: dict) -> ToolResult:
        self.calls.append((name, args))
        return ToolResult(ok=True, data={"echoed": args})


class _FakeProvider:
    """Yields scripted neutral events; one script per ``complete`` call."""

    def __init__(self, scripts: list[list[ProviderEvent]]) -> None:
        self._scripts = list(scripts)
        self.calls: list[dict] = []

    async def complete(self, *, system, messages, tools, model, max_tokens) -> AsyncIterator:
        self.calls.append({"messages": messages, "tools": tools, "system": system})
        for ev in self._scripts.pop(0):
            yield ev


async def _noop(ctx, params):  # tool handler placeholder
    return {}


def _tool(name: str, category: ToolCategory, *, free_text: bool = False) -> Tool:
    return Tool(
        name=name,
        description=f"{name} tool",
        parameters=_Args,
        handler=_noop,
        permissions=[],
        category=category,
        exposes_free_text=free_text,
    )


def _ctx(registry: _FakeRegistry) -> AgentContext:
    return AgentContext(
        agent_id=uuid4(),
        session_id=uuid4(),
        clinic_id=uuid4(),
        mode=AgentMode.AUTONOMOUS,
        permissions=["*"],
        tools=registry,  # type: ignore[arg-type]
        db=None,  # type: ignore[arg-type]
    )


async def _collect(gen) -> list:
    return [ev async for ev in gen]


@pytest.mark.asyncio
async def test_simple_text_turn_yields_final_and_usage() -> None:
    reg = _FakeRegistry({})
    provider = _FakeProvider([[TextDelta("hola "), TextDelta("mundo"), Usage(10, 5), Done("stop")]])
    history = [ProviderMessage(Role.USER, [TextBlock("hi")])]

    events = await _collect(
        run_turn(
            ctx=_ctx(reg),
            provider=provider,
            system="s",
            history=history,
            tool_names=[],
            redactor=Redactor(enabled=False),
            model="gpt-4.1",
        )
    )

    tokens = [e for e in events if isinstance(e, Token)]
    assert "".join(t.text for t in tokens) == "hola mundo"
    assert any(isinstance(e, TurnUsage) and e.input_tokens == 10 for e in events)
    assert isinstance(events[-1], Final)
    # assistant turn appended in real space
    assert history[-1].role is Role.ASSISTANT


@pytest.mark.asyncio
async def test_read_tool_executes_then_answers() -> None:
    reg = _FakeRegistry({"m.echo": _tool("echo", ToolCategory.READ)})
    provider = _FakeProvider(
        [
            [ToolUse("c1", "m.echo", {"q": "x"}), Done("tool_calls")],
            [TextDelta("listo"), Done("stop")],
        ]
    )
    history = [ProviderMessage(Role.USER, [TextBlock("haz x")])]

    events = await _collect(
        run_turn(
            ctx=_ctx(reg),
            provider=provider,
            system="s",
            history=history,
            tool_names=["m.echo"],
            redactor=Redactor(enabled=False),
            model="gpt-4.1",
        )
    )

    assert reg.calls == [("m.echo", {"q": "x"})]
    assert any(isinstance(e, ToolCallStarted) for e in events)
    assert any(isinstance(e, ToolCallFinished) and e.ok for e in events)
    assert isinstance(events[-1], Final)


@pytest.mark.asyncio
async def test_write_tool_suspends_without_executing() -> None:
    reg = _FakeRegistry({"m.book": _tool("book", ToolCategory.WRITE)})
    provider = _FakeProvider([[ToolUse("c2", "m.book", {"q": "mañana"}), Done("tool_calls")]])
    history = [ProviderMessage(Role.USER, [TextBlock("agenda")])]

    events = await _collect(
        run_turn(
            ctx=_ctx(reg),
            provider=provider,
            system="s",
            history=history,
            tool_names=["m.book"],
            redactor=Redactor(enabled=False),
            model="gpt-4.1",
        )
    )

    assert reg.calls == []  # never executed
    assert isinstance(events[-1], ConfirmationRequired)
    assert events[-1].name == "m.book"
    # pending tool_use persisted on the assistant message
    assert history[-1].role is Role.ASSISTANT


@pytest.mark.asyncio
async def test_free_text_tool_excluded_under_redaction() -> None:
    reg = _FakeRegistry(
        {
            "m.read": _tool("read", ToolCategory.READ),
            "m.summary": _tool("summary", ToolCategory.READ, free_text=True),
        }
    )
    provider = _FakeProvider([[TextDelta("ok"), Done("stop")]])
    history = [ProviderMessage(Role.USER, [TextBlock("hi")])]

    await _collect(
        run_turn(
            ctx=_ctx(reg),
            provider=provider,
            system="s",
            history=history,
            tool_names=["m.read", "m.summary"],
            redactor=Redactor(enabled=True),
            model="gpt-4.1",
        )
    )

    offered = {t["function"]["name"] for t in provider.calls[0]["tools"]}
    assert offered == {"m.read"}  # free-text tool dropped from cloud path


@pytest.mark.asyncio
async def test_budget_exceeded_short_circuits() -> None:
    class _Broke:
        def check(self) -> bool:
            return False

        def record(self, i: int, o: int) -> None:
            pass

    reg = _FakeRegistry({})
    provider = _FakeProvider([[TextDelta("never"), Done("stop")]])
    history = [ProviderMessage(Role.USER, [TextBlock("hi")])]

    events = await _collect(
        run_turn(
            ctx=_ctx(reg),
            provider=provider,
            system="s",
            history=history,
            tool_names=[],
            redactor=Redactor(enabled=False),
            model="gpt-4.1",
            budget=_Broke(),
        )
    )

    assert len(events) == 1 and isinstance(events[0], BudgetExceeded)
    assert provider.calls == []  # provider never invoked


# --- redaction unit ------------------------------------------------------


def test_redactor_tokenizes_and_restores() -> None:
    r = Redactor(enabled=True)
    msg = ProviderMessage(
        Role.TOOL,
        [ToolResultBlock("c1", {"full_name": "María González", "phone": "600123123"})],
    )
    out = r.redact_outgoing([msg])
    block = out[0].content[0]
    assert block.content["full_name"] != "María González"
    assert block.content["phone"] != "600123123"
    # deterministic + reversible
    token = block.content["full_name"]
    assert r.rehydrate(token) == "María González"
    assert r.resolve_args({"who": token}) == {"who": "María González"}


def test_redactor_disabled_is_identity() -> None:
    r = Redactor(enabled=False)
    msg = ProviderMessage(Role.TOOL, [ToolResultBlock("c1", {"full_name": "Ana"})])
    assert r.redact_outgoing([msg]) is not None
    assert r.redact_outgoing([msg])[0].content[0].content == {"full_name": "Ana"}


def test_redactor_replaces_known_entity_in_free_text() -> None:
    r = Redactor(enabled=True)
    token = r.table.tokenize("María González", "NAME")
    redacted = r.redact_outgoing(
        [ProviderMessage(Role.USER, [TextBlock("agenda a María González")])]
    )
    assert token in redacted[0].content[0].text
    assert "María González" not in redacted[0].content[0].text


# --- factory -------------------------------------------------------------


def test_factory_rejects_unsupported_provider() -> None:
    with pytest.raises(LLMConfigError):
        get_provider("anthropic")


def test_openai_name_roundtrip() -> None:
    # OpenAI rejects dots in function names; the provider maps . <-> -.
    from app.core.llm.openai_provider import _from_openai_name, _to_openai_name

    for qualified in ("patients.search_patients", "agenda.get_day_overview"):
        safe = _to_openai_name(qualified)
        assert "." not in safe
        assert _from_openai_name(safe) == qualified


def test_openai_provider_requires_key() -> None:
    # The factory falls back to settings.OPENAI_API_KEY, so test the
    # provider's own guard directly with no key available.
    from app.core.llm.openai_provider import OpenAIProvider

    with pytest.raises(LLMConfigError):
        OpenAIProvider(api_key="")
