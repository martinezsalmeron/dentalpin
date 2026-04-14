"""Pydantic schemas for media module."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

DocumentType = Literal["consent", "id_scan", "insurance", "report", "referral", "other"]


class DocumentCreate(BaseModel):
    """Schema for creating a document (metadata only, file separate)."""

    document_type: DocumentType
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class DocumentUpdate(BaseModel):
    """Schema for updating document metadata."""

    document_type: DocumentType | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class UploaderBrief(BaseModel):
    """Brief uploader info."""

    id: UUID
    first_name: str
    last_name: str

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    """Schema for document response."""

    id: UUID
    patient_id: UUID
    document_type: str
    title: str
    description: str | None
    original_filename: str
    mime_type: str
    file_size: int
    status: str
    uploaded_by: UUID
    uploader: UploaderBrief | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentBrief(BaseModel):
    """Brief document info for lists."""

    id: UUID
    document_type: str
    title: str
    original_filename: str
    mime_type: str
    file_size: int
    created_at: datetime

    class Config:
        from_attributes = True
