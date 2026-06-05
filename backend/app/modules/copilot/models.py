"""Copilot module — conversation persistence + per-clinic config.

Three tables on the ``copilot`` Alembic branch:

* ``copilot_conversations`` — one chat session, linked to a core
  ``agent_sessions`` row so every tool call lands in
  ``agent_audit_logs``.
* ``copilot_messages`` — the turn-by-turn transcript in **real space**
  (the redactor tokenizes only on the way to the provider). The source
  of truth for resuming a suspended turn: an assistant ``tool_use``
  block with no matching ``tool_result`` means "awaiting confirmation".
* ``copilot_settings`` — per-clinic provider/model/budget, lazy-created.

Cross-module FK is limited to ``agent_sessions`` / ``clinics`` / ``users``
(all core), so the module keeps ``depends = []``.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, TimestampMixin


class CopilotConversation(Base, TimestampMixin):
    __tablename__ = "copilot_conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Link to the core agent session so tool calls audit-trail correctly.
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_sessions.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    context: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    provider: Mapped[str] = mapped_column(String(20), nullable=False, default="openai")
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    total_input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class CopilotMessage(Base):
    __tablename__ = "copilot_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("copilot_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    clinic_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    # Monotonic per-conversation ordinal: assistant + tool messages in the
    # same turn share a timestamp, so order must not depend on created_at.
    seq: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # system | user | assistant | tool
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    # Neutral content blocks serialized to JSON (see bridge serde).
    content: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CopilotSettings(Base):
    __tablename__ = "copilot_settings"

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id", ondelete="CASCADE"), primary_key=True
    )
    provider: Mapped[str] = mapped_column(String(20), nullable=False, default="openai")
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    redaction_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # NULL → no ceiling.
    monthly_token_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    monthly_cost_limit_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    period_output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    period_cost_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
