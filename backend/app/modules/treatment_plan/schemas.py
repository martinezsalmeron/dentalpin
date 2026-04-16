"""Treatment plan module Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Brief/nested response schemas (for embedding in other responses)
# ---------------------------------------------------------------------------


class PatientBrief(BaseModel):
    """Brief patient info for embedding in responses."""

    id: UUID
    first_name: str
    last_name: str

    class Config:
        from_attributes = True


class BudgetBrief(BaseModel):
    """Brief budget info for embedding in responses."""

    id: UUID
    budget_number: str
    status: str
    total: float

    class Config:
        from_attributes = True


class ToothTreatmentBrief(BaseModel):
    """Brief tooth treatment info for embedding in responses."""

    id: UUID
    tooth_number: int
    treatment_type: str
    status: str
    surfaces: list[str] | None = None

    class Config:
        from_attributes = True


class CatalogItemBrief(BaseModel):
    """Brief catalog item info for embedding in responses."""

    id: UUID
    internal_code: str
    names: dict
    default_price: float | None = None

    class Config:
        from_attributes = True


class TreatmentMediaResponse(BaseModel):
    """Response for treatment media."""

    id: UUID
    document_id: UUID
    media_type: str
    display_order: int
    notes: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Treatment Plan schemas
# ---------------------------------------------------------------------------


class TreatmentPlanCreate(BaseModel):
    """Schema for creating a treatment plan."""

    patient_id: UUID
    title: str | None = Field(default=None, max_length=200)
    assigned_professional_id: UUID | None = None
    diagnosis_notes: str | None = None
    internal_notes: str | None = None


class TreatmentPlanUpdate(BaseModel):
    """Schema for updating a treatment plan."""

    title: str | None = Field(default=None, max_length=200)
    assigned_professional_id: UUID | None = None
    diagnosis_notes: str | None = None
    internal_notes: str | None = None


class TreatmentPlanStatusUpdate(BaseModel):
    """Schema for changing plan status."""

    status: str = Field(..., pattern="^(draft|active|completed|archived|cancelled)$")


class TreatmentPlanResponse(BaseModel):
    """Response schema for treatment plan list."""

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

    class Config:
        from_attributes = True


class TreatmentPlanDetailResponse(TreatmentPlanResponse):
    """Detailed response with nested items and relations."""

    diagnosis_notes: str | None
    internal_notes: str | None
    items: list["PlannedTreatmentItemResponse"] = []
    patient: PatientBrief | None = None
    budget: BudgetBrief | None = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Planned Treatment Item schemas
# ---------------------------------------------------------------------------


class PlannedTreatmentItemCreate(BaseModel):
    """Schema for adding a treatment to a plan."""

    # For tooth-specific treatments
    tooth_treatment_id: UUID | None = None

    # For global treatments (or to specify catalog item)
    catalog_item_id: UUID | None = None
    is_global: bool = False

    # Optional fields
    sequence_order: int | None = None
    notes: str | None = None


class PlannedTreatmentItemUpdate(BaseModel):
    """Schema for updating a planned treatment item."""

    sequence_order: int | None = None
    notes: str | None = None


class PlannedTreatmentItemResponse(BaseModel):
    """Response schema for planned treatment item."""

    id: UUID
    clinic_id: UUID
    treatment_plan_id: UUID
    tooth_treatment_id: UUID | None
    catalog_item_id: UUID | None
    is_global: bool
    sequence_order: int
    status: str
    completed_without_appointment: bool
    completed_at: datetime | None
    completed_by: UUID | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    # Nested data
    tooth_treatment: ToothTreatmentBrief | None = None
    catalog_item: CatalogItemBrief | None = None
    media: list[TreatmentMediaResponse] = []

    class Config:
        from_attributes = True


class CompleteItemRequest(BaseModel):
    """Request to mark an item as completed."""

    completed_without_appointment: bool = True
    notes: str | None = None


# ---------------------------------------------------------------------------
# Budget integration schemas
# ---------------------------------------------------------------------------


class LinkBudgetRequest(BaseModel):
    """Request to link a budget to the plan."""

    budget_id: UUID


class GenerateBudgetResponse(BaseModel):
    """Response after generating a budget from the plan."""

    budget_id: UUID
    budget_number: str


# ---------------------------------------------------------------------------
# Media schemas
# ---------------------------------------------------------------------------


class TreatmentMediaCreate(BaseModel):
    """Schema for adding media to a treatment item."""

    document_id: UUID
    media_type: str = Field(..., pattern="^(before|after|xray|reference)$")
    display_order: int = 0
    notes: str | None = None


# Update forward references
TreatmentPlanDetailResponse.model_rebuild()
