"""Orchestrator bridge — wires a conversation to the core engine.

Builds the :class:`AgentContext` (permissions = the caller's own, a
guardrail config that defers writes to inline confirmation, audit linked
to the core agent session), reconstructs the message history, drives
``run_turn``, persists the new messages, and yields ``TurnEvent``s that
the router frames as SSE. Provider is injectable for tests.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.agents.context import AgentContext, AgentMode
from app.core.agents.guardrails import GuardrailConfig
from app.core.agents.orchestrator import ConfirmationRequired, ToolCallFinished, TurnUsage, run_turn
from app.core.agents.redaction import Redactor
from app.core.agents.tools.registry import tool_registry
from app.core.auth.permissions import permission_matches
from app.core.llm.base import ProviderMessage, Role, TextBlock, ToolResultBlock, ToolUseBlock
from app.core.llm.factory import get_provider

from .models import CopilotConversation, CopilotSettings
from .serde import message_from_row
from .service import ClinicBudgetGuard, ConversationService

SYSTEM_PROMPT = (
    "Eres el copiloto de DentalPin, asistente de una clínica dental. "
    "Respondes en español, con concisión y precisión. Usa las herramientas "
    "disponibles para consultar y actuar sobre los datos de la clínica; no "
    "inventes información que no provenga de una herramienta. Para acciones "
    "que modifican datos (crear, reservar, cancelar) llama a la herramienta "
    "correspondiente: el sistema pedirá confirmación al usuario antes de "
    "ejecutarla. Nunca asumas permisos que no tengas. "
    "Lo facturado y lo cobrado son ejes contables separados: NUNCA "
    "calcules, restes ni muestres la diferencia entre ellos (deuda, "
    "pendiente, morosidad). Informa cada eje por separado si te lo piden."
)

# Copilot gates writes via inline confirmation (a turn-level pause), so
# the approval-queue triggers are disabled. Rate limits + denylist stay.
COPILOT_GUARDRAILS = GuardrailConfig(
    require_approval_for=[],
    auto_require_approval_for_destructive=False,
    blocked_tools=[],
)


def _tool_names_for(permissions: list[str]) -> list[str]:
    """Registry tools the caller is allowed to use (AND of permissions)."""
    out: list[str] = []
    for name in tool_registry.list():
        tool = tool_registry.get(name)
        if tool is None:
            continue
        if all(
            any(permission_matches(req, granted) for granted in permissions)
            for req in tool.permissions
        ):
            out.append(name)
    return out


def _build_context(
    *,
    db: AsyncSession,
    clinic_id: UUID,
    permissions: list[str],
    user_id: UUID,
    agent_id: UUID,
    session_id: UUID,
) -> AgentContext:
    return AgentContext(
        agent_id=agent_id,
        session_id=session_id,
        clinic_id=clinic_id,
        mode=AgentMode.AUTONOMOUS,  # writes gated by inline confirm, not the queue
        permissions=permissions,
        tools=tool_registry,
        db=db,
        supervisor_id=user_id,
        guardrail_config=COPILOT_GUARDRAILS,
    )


def _redactor_for(conv: CopilotConversation, settings_row: CopilotSettings) -> Redactor:
    r = Redactor(enabled=settings_row.redaction_enabled)
    r.seed(conv.context)
    return r


async def _history(db: AsyncSession, conv: CopilotConversation) -> list[ProviderMessage]:
    rows = await ConversationService.list_messages(db, conv.id)
    return [message_from_row(m.role, m.content) for m in rows]


async def _persist_tail(
    db: AsyncSession, conv: CopilotConversation, history: list[ProviderMessage], start: int
) -> None:
    for msg in history[start:]:
        await ConversationService.append_message(db, conv, role=msg.role.value, blocks=msg.content)


async def drive_turn(
    *,
    db: AsyncSession,
    conv: CopilotConversation,
    settings_row: CopilotSettings,
    permissions: list[str],
    user_id: UUID,
    agent_id: UUID,
    session_id: UUID,
    user_text: str,
    provider=None,
) -> AsyncIterator:
    """Append the user message, run one turn, persist + yield events."""
    history = await _history(db, conv)
    user_msg = ProviderMessage(Role.USER, [TextBlock(user_text)])
    await ConversationService.append_message(db, conv, role="user", blocks=user_msg.content)
    history.append(user_msg)

    provider = provider or get_provider(conv.provider)
    redactor = _redactor_for(conv, settings_row)
    budget = ClinicBudgetGuard(settings_row, conv)
    ctx = _build_context(
        db=db,
        clinic_id=conv.clinic_id,
        permissions=permissions,
        user_id=user_id,
        agent_id=agent_id,
        session_id=session_id,
    )

    start = len(history)
    async for ev in run_turn(
        ctx=ctx,
        provider=provider,
        system=SYSTEM_PROMPT,
        history=history,
        tool_names=_tool_names_for(permissions),
        redactor=redactor,
        model=conv.model,
        max_tokens=4096,
        budget=budget,
    ):
        yield ev
    await _persist_tail(db, conv, history, start)


async def resume_turn(
    *,
    db: AsyncSession,
    conv: CopilotConversation,
    settings_row: CopilotSettings,
    permissions: list[str],
    user_id: UUID,
    agent_id: UUID,
    session_id: UUID,
    call_id: str,
    approve: bool,
    provider=None,
) -> AsyncIterator:
    """Execute (or skip) the pending tool, then resume the turn."""
    history = await _history(db, conv)
    pending = _find_pending(history, call_id)
    if pending is None:
        return

    provider = provider or get_provider(conv.provider)
    redactor = _redactor_for(conv, settings_row)
    budget = ClinicBudgetGuard(settings_row, conv)
    ctx = _build_context(
        db=db,
        clinic_id=conv.clinic_id,
        permissions=permissions,
        user_id=user_id,
        agent_id=agent_id,
        session_id=session_id,
    )

    if approve:
        res = await ctx.tools.call(ctx, pending.name, pending.input)
        payload = res.data if res.ok else {"error": res.error}
        is_error = not res.ok
        yield ToolCallFinished(call_id, pending.name, res.ok, payload)
    else:
        payload = {"status": "cancelled_by_user"}
        is_error = False

    tool_msg = ProviderMessage(Role.TOOL, [ToolResultBlock(call_id, payload, is_error)])
    history.append(tool_msg)
    await ConversationService.append_message(db, conv, role="tool", blocks=tool_msg.content)

    start = len(history)
    async for ev in run_turn(
        ctx=ctx,
        provider=provider,
        system=SYSTEM_PROMPT,
        history=history,
        tool_names=_tool_names_for(permissions),
        redactor=redactor,
        model=conv.model,
        max_tokens=4096,
        budget=budget,
    ):
        yield ev
    await _persist_tail(db, conv, history, start)


def _find_pending(history: list[ProviderMessage], call_id: str) -> ToolUseBlock | None:
    for msg in reversed(history):
        if msg.role is Role.ASSISTANT:
            for block in msg.content:
                if isinstance(block, ToolUseBlock) and block.id == call_id:
                    return block
    return None


__all__ = ["drive_turn", "resume_turn", "ConfirmationRequired", "TurnUsage"]
