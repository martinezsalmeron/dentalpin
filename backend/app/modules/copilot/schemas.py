"""Copilot Pydantic schemas (non-SSE endpoints)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SessionCreate(BaseModel):
    context: dict[str, Any] = Field(default_factory=dict)


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str | None
    status: str
    provider: str
    model: str
    total_input_tokens: int
    total_output_tokens: int
    created_at: datetime
    updated_at: datetime


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=8000)


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: str
    content: list[dict[str, Any]]
    created_at: datetime


class ConfirmRequest(BaseModel):
    decision: Literal["confirm", "reject"]


class SettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    provider: str
    model: str
    redaction_enabled: bool
    monthly_token_limit: int | None
    monthly_cost_limit_cents: int | None
    period_input_tokens: int
    period_output_tokens: int


class SettingsUpdate(BaseModel):
    provider: str | None = None
    model: str | None = None
    redaction_enabled: bool | None = None
    monthly_token_limit: int | None = None
    monthly_cost_limit_cents: int | None = None
