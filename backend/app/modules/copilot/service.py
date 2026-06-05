"""Copilot service layer — conversations, messages, settings, budget."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings as app_settings
from app.core.llm.base import ContentBlock

from .models import CopilotConversation, CopilotMessage, CopilotSettings
from .serde import content_to_json


class CopilotSettingsService:
    """Per-clinic provider/model/budget, lazy-created on first read."""

    @staticmethod
    async def get_or_create(db: AsyncSession, clinic_id: UUID) -> CopilotSettings:
        row = await db.get(CopilotSettings, clinic_id)
        if row is not None:
            return CopilotSettingsService._roll_period(row)
        row = CopilotSettings(
            clinic_id=clinic_id,
            provider=app_settings.COPILOT_PROVIDER_DEFAULT,
            model=app_settings.COPILOT_MODEL_CHAT_OPENAI,
            redaction_enabled=app_settings.COPILOT_REDACTION_DEFAULT,
            period_start=datetime.now(UTC).date().replace(day=1),
        )
        db.add(row)
        await db.flush()
        return row

    @staticmethod
    def _roll_period(row: CopilotSettings) -> CopilotSettings:
        """Reset monthly counters when the calendar month has changed."""
        first_of_month = datetime.now(UTC).date().replace(day=1)
        if row.period_start != first_of_month:
            row.period_start = first_of_month
            row.period_input_tokens = 0
            row.period_output_tokens = 0
            row.period_cost_cents = 0
        return row

    @staticmethod
    async def update(db: AsyncSession, clinic_id: UUID, data: dict[str, Any]) -> CopilotSettings:
        row = await CopilotSettingsService.get_or_create(db, clinic_id)
        provider = data.get("provider", row.provider)
        if provider == "openai" and not app_settings.OPENAI_API_KEY:
            raise ValueError("OpenAI provider selected but OPENAI_API_KEY is not configured")
        for field in (
            "provider",
            "model",
            "redaction_enabled",
            "monthly_token_limit",
            "monthly_cost_limit_cents",
        ):
            if field in data and data[field] is not None:
                setattr(row, field, data[field])
        await db.flush()
        return row


class ConversationService:
    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        clinic_id: UUID,
        user_id: UUID,
        provider: str,
        model: str,
        context: dict | None = None,
        session_id: UUID | None = None,
    ) -> CopilotConversation:
        conv = CopilotConversation(
            clinic_id=clinic_id,
            user_id=user_id,
            provider=provider,
            model=model,
            context=context or {},
            session_id=session_id,
        )
        db.add(conv)
        await db.flush()
        return conv

    @staticmethod
    async def get(
        db: AsyncSession, clinic_id: UUID, conversation_id: UUID, *, user_id: UUID | None = None
    ) -> CopilotConversation | None:
        conv = await db.get(CopilotConversation, conversation_id)
        if conv is None or conv.clinic_id != clinic_id:
            return None
        if user_id is not None and conv.user_id != user_id:
            return None
        return conv

    @staticmethod
    async def list(
        db: AsyncSession,
        clinic_id: UUID,
        *,
        user_id: UUID | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[CopilotConversation], int]:
        page_size = min(max(page_size, 1), 100)
        conditions = [CopilotConversation.clinic_id == clinic_id]
        if user_id is not None:
            conditions.append(CopilotConversation.user_id == user_id)
        total = await db.scalar(
            select(func.count()).select_from(CopilotConversation).where(*conditions)
        )
        rows = (
            (
                await db.execute(
                    select(CopilotConversation)
                    .where(*conditions)
                    .order_by(CopilotConversation.updated_at.desc())
                    .limit(page_size)
                    .offset((page - 1) * page_size)
                )
            )
            .scalars()
            .all()
        )
        return list(rows), int(total or 0)

    @staticmethod
    async def list_messages(db: AsyncSession, conversation_id: UUID) -> list[CopilotMessage]:
        rows = (
            (
                await db.execute(
                    select(CopilotMessage)
                    .where(CopilotMessage.conversation_id == conversation_id)
                    .order_by(CopilotMessage.seq.asc())
                )
            )
            .scalars()
            .all()
        )
        return list(rows)

    @staticmethod
    async def _next_seq(db: AsyncSession, conversation_id: UUID) -> int:
        current = await db.scalar(
            select(func.max(CopilotMessage.seq)).where(
                CopilotMessage.conversation_id == conversation_id
            )
        )
        return int(current or 0) + 1

    @staticmethod
    async def append_message(
        db: AsyncSession,
        conv: CopilotConversation,
        *,
        role: str,
        blocks: list[ContentBlock],
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> CopilotMessage:
        msg = CopilotMessage(
            conversation_id=conv.id,
            clinic_id=conv.clinic_id,
            seq=await ConversationService._next_seq(db, conv.id),
            role=role,
            content=content_to_json(blocks),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        db.add(msg)
        await db.flush()
        return msg


class ClinicBudgetGuard:
    """BudgetGuard backed by ``copilot_settings`` monthly token counters.

    Mutates the settings + conversation rows in place; the caller commits.
    Cost accounting is token-based in v1 (cost_cents stays 0 without a
    pricing table).
    """

    def __init__(self, settings_row: CopilotSettings, conv: CopilotConversation) -> None:
        self._s = settings_row
        self._conv = conv
        self.threshold_crossed = False

    def check(self) -> bool:
        limit = self._s.monthly_token_limit
        if limit is None:
            return True
        used = self._s.period_input_tokens + self._s.period_output_tokens
        return used < limit

    def record(self, input_tokens: int, output_tokens: int) -> None:
        self._s.period_input_tokens += input_tokens
        self._s.period_output_tokens += output_tokens
        self._conv.total_input_tokens += input_tokens
        self._conv.total_output_tokens += output_tokens
        limit = self._s.monthly_token_limit
        if limit:
            used = self._s.period_input_tokens + self._s.period_output_tokens
            if used >= int(limit * 0.8):
                self.threshold_crossed = True
