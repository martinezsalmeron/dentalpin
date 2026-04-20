"""Timeline schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TimelineEntry(BaseModel):
    id: UUID
    event_type: str
    event_category: str
    source_table: str
    source_id: UUID
    title: str
    description: str | None = None
    event_data: dict | None = None
    occurred_at: datetime
    created_by: UUID | None = None

    class Config:
        from_attributes = True


class TimelineResponse(BaseModel):
    entries: list[TimelineEntry]
    total: int
    page: int
    page_size: int
    has_more: bool
