"""Pydantic schemas for media module."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

DocumentType = Literal["consent", "id_scan", "insurance", "report", "referral", "other"]

# --- Document base schemas (pre-existing API surface) -------------------


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

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    first_name: str
    last_name: str


class DocumentResponse(BaseModel):
    """Full document response. Includes media taxonomy + signed URLs."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    patient_id: UUID
    document_type: str
    title: str
    description: str | None
    original_filename: str
    mime_type: str
    file_size: int
    status: str

    # Media taxonomy
    media_kind: str
    media_category: str | None
    media_subtype: str | None
    captured_at: datetime | None
    paired_document_id: UUID | None
    tags: list[str]

    # Audit
    uploaded_by: UUID
    uploader: UploaderBrief | None = None
    created_at: datetime
    updated_at: datetime

    # URLs derived in the router (None for non-thumbnailable kinds).
    thumb_url: str | None = None
    medium_url: str | None = None
    full_url: str | None = None


class DocumentBrief(BaseModel):
    """Brief document info for lists."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_type: str
    title: str
    original_filename: str
    mime_type: str
    file_size: int
    media_kind: str
    media_category: str | None = None
    media_subtype: str | None = None
    created_at: datetime


# --- Photo taxonomy schemas --------------------------------------------


class PhotoMetadataUpdate(BaseModel):
    """Patch the photo classification of an existing document."""

    media_category: str | None = None
    media_subtype: str | None = None
    captured_at: datetime | None = None
    tags: list[str] | None = None
    paired_document_id: UUID | None = None


# --- Polymorphic attachment schemas ------------------------------------


class AttachmentCreate(BaseModel):
    """Link an existing Document to an arbitrary owner."""

    document_id: UUID
    owner_type: str = Field(min_length=1, max_length=40)
    owner_id: UUID
    display_order: int = 0


class AttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    owner_type: str
    owner_id: UUID
    display_order: int
    created_at: datetime
    document: DocumentBrief | None = None
    thumb_url: str | None = None
