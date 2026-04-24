"""Treatment plan module Pydantic schemas."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Nested brief schemas
# ---------------------------------------------------------------------------


class PatientBrief(BaseModel):
    """Brief patient info."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    first_name: str
    last_name: str


class BudgetBrief(BaseModel):
    """Brief budget info."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    budget_number: str
    status: str
    total: float


class TreatmentToothBrief(BaseModel):
    """Per-tooth member of a Treatment, embedded in plan items."""

    model_config = ConfigDict(from_attributes=True)

    tooth_number: int
    role: str | None = None
    surfaces: list[str] | None = None


class CatalogItemBrief(BaseModel):
    """Brief catalog item info."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    internal_code: str
    names: dict
    default_price: float | None = None


class TreatmentBrief(BaseModel):
    """Brief Treatment info (header + teeth)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinical_type: str
    scope: str
    arch: str | None = None
    status: str
    catalog_item_id: UUID | None = None
    catalog_item: CatalogItemBrief | None = None
    price_snapshot: Decimal | None = None
    currency_snapshot: str | None = None
    teeth: list[TreatmentToothBrief] = Field(default_factory=list)


class TreatmentMediaResponse(BaseModel):
    """Response for treatment media."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    media_type: str
    display_order: int
    notes: str | None = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Treatment Plan schemas
# ---------------------------------------------------------------------------


class TreatmentPlanCreate(BaseModel):
    """Create a treatment plan."""

    patient_id: UUID
    title: str | None = Field(default=None, max_length=200)
    assigned_professional_id: UUID | None = None
    diagnosis_notes: str | None = None
    internal_notes: str | None = None


class TreatmentPlanUpdate(BaseModel):
    """Update a treatment plan."""

    title: str | None = Field(default=None, max_length=200)
    assigned_professional_id: UUID | None = None
    diagnosis_notes: str | None = None
    internal_notes: str | None = None


class TreatmentPlanStatusUpdate(BaseModel):
    """Change plan status."""

    status: str = Field(..., pattern="^(draft|active|completed|archived|cancelled)$")


class TreatmentPlanResponse(BaseModel):
    """Response for treatment plan list."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID
    patient_id: UUID
    plan_number: str
    title: str | None
    status: str
    budget_id: UUID | None
    assigned_professional_id: UUID | None
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    item_count: int = 0
    completed_count: int = 0
    total: float = 0.0
    patient: PatientBrief | None = None
    budget: BudgetBrief | None = None


class TreatmentPlanDetailResponse(TreatmentPlanResponse):
    """Detailed response with nested items."""

    diagnosis_notes: str | None = None
    internal_notes: str | None = None
    items: list["PlannedTreatmentItemResponse"] = []


# ---------------------------------------------------------------------------
# Planned treatment item schemas
# ---------------------------------------------------------------------------


class PlannedTreatmentItemCreate(BaseModel):
    """Add a treatment to a plan by Treatment id."""

    treatment_id: UUID
    sequence_order: int | None = None
    notes: str | None = None


class PlannedTreatmentItemUpdate(BaseModel):
    """Update a planned treatment item (scheduling metadata only)."""

    sequence_order: int | None = None
    notes: str | None = None


class PlannedTreatmentItemResponse(BaseModel):
    """Response for planned treatment item."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID
    treatment_plan_id: UUID
    treatment_id: UUID
    sequence_order: int
    status: str
    completed_without_appointment: bool
    completed_at: datetime | None
    completed_by: UUID | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    # Embedded Treatment + optional catalog item.
    treatment: TreatmentBrief | None = None
    catalog_item: CatalogItemBrief | None = None
    media: list[TreatmentMediaResponse] = []


class CompleteItemRequest(BaseModel):
    """Mark an item as completed.

    ``note_body`` (rich-text HTML, optional) creates a new ``clinical_notes``
    entry at plan_item level. When empty/absent, a ``item_completed_without_note``
    event is published so the audit timeline can record the skip.
    ``attachment_document_ids`` lets the caller link already-uploaded documents
    to the newly-created note in the same transaction.
    """

    completed_without_appointment: bool = True
    notes: str | None = None
    note_body: str | None = None
    attachment_document_ids: list[UUID] = Field(default_factory=list)


class ReorderItemsRequest(BaseModel):
    """Reorder all items of a plan in a single atomic update.

    `item_ids` MUST cover exactly the plan's current items — no missing, no extras.
    `sequence_order` is rewritten as 0, 1, 2, ... in the given order.
    """

    item_ids: list[UUID]


# ---------------------------------------------------------------------------
# Budget integration schemas
# ---------------------------------------------------------------------------


class LinkBudgetRequest(BaseModel):
    budget_id: UUID


class GenerateBudgetResponse(BaseModel):
    budget_id: UUID
    budget_number: str


# ---------------------------------------------------------------------------
# Media schemas
# ---------------------------------------------------------------------------


class TreatmentMediaCreate(BaseModel):
    document_id: UUID
    media_type: str = Field(..., pattern="^(before|after|xray|reference)$")
    display_order: int = 0
    notes: str | None = None


# ---------------------------------------------------------------------------
# Clinical notes + polymorphic attachments
# ---------------------------------------------------------------------------


class NoteAttachmentResponse(BaseModel):
    """Response for a single polymorphic note attachment."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    owner_type: str
    owner_id: UUID
    note_id: UUID | None
    display_order: int
    created_at: datetime


class ClinicalNoteCreate(BaseModel):
    """Create a clinical note for a plan or plan_item.

    ``attachment_document_ids`` references Documents already uploaded through
    the media module. The service validates that every document belongs to
    the same patient as the owner.
    """

    owner_type: str = Field(..., pattern="^(plan|plan_item)$")
    owner_id: UUID
    body: str = Field(..., min_length=1)
    attachment_document_ids: list[UUID] = Field(default_factory=list)


class ClinicalNoteUpdate(BaseModel):
    """Edit a note body. Author or admin only."""

    body: str = Field(..., min_length=1)


class ClinicalNoteResponse(BaseModel):
    """Response for a single clinical note (plan or plan_item scope)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID
    owner_type: str
    owner_id: UUID
    body: str
    author_id: UUID
    created_at: datetime
    updated_at: datetime
    attachments: list[NoteAttachmentResponse] = Field(default_factory=list)


class NoteAttachmentCreate(BaseModel):
    """Link an existing Document to an owner, with optional note attribution."""

    owner_type: str = Field(..., pattern="^(plan|plan_item|appointment_treatment)$")
    owner_id: UUID
    document_id: UUID
    note_id: UUID | None = None
    display_order: int = 0


class ClinicalNoteEntry(BaseModel):
    """Merged-feed entry covering plan / plan_item / visit notes.

    Used by ``GET /plans/{id}/clinical-notes``. ``source`` tells the UI where
    the note lives; visit notes have no ``note_id`` because they live on
    ``AppointmentTreatment.notes`` (agenda module).

    ``plan_item_id`` is populated for ``plan_item`` (== owner_id) and ``visit``
    (from ``AppointmentTreatment.planned_treatment_item_id``) so the UI can
    group entries under the corresponding treatment without additional lookups.
    """

    source: str  # 'plan' | 'plan_item' | 'visit'
    note_id: UUID | None
    owner_id: UUID
    plan_item_id: UUID | None = None
    body: str
    author_id: UUID | None
    created_at: datetime
    updated_at: datetime | None = None
    attachments: list[NoteAttachmentResponse] = Field(default_factory=list)


class PlanItemNotesGroup(BaseModel):
    """Plan item + its plan_item and visit notes."""

    plan_item: PlannedTreatmentItemResponse
    notes: list[ClinicalNoteEntry] = Field(default_factory=list)


class PlanNotesGroup(BaseModel):
    """One plan block of the patient clinical-notes feed."""

    plan: TreatmentPlanResponse
    plan_notes: list[ClinicalNoteEntry] = Field(default_factory=list)
    treatments: list[PlanItemNotesGroup] = Field(default_factory=list)


class NoteTemplateResponse(BaseModel):
    """One entry of the static template catalog."""

    id: str
    category: str
    i18n_key: str
    body: str


TreatmentPlanDetailResponse.model_rebuild()
