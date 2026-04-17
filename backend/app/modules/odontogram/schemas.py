"""Pydantic schemas for odontogram module."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .constants import (
    CONDITION_COLORS,
    SURFACE_TREATMENTS,
    SURFACES,
    WHOLE_TOOTH_TREATMENTS,
    ToothCondition,
    TreatmentStatus,
    is_valid_tooth_number,
    is_valid_treatment_type,
)


class SurfaceUpdate(BaseModel):
    """Update for a single surface."""

    surface: str = Field(..., description="Surface code: M, D, O, V, or L")
    condition: str = Field(..., description="Condition to set")

    @field_validator("surface")
    @classmethod
    def validate_surface(cls, v: str) -> str:
        if v not in SURFACES:
            raise ValueError(f"Invalid surface: {v}. Must be one of {SURFACES}")
        return v

    @field_validator("condition")
    @classmethod
    def validate_condition(cls, v: str) -> str:
        valid_conditions = [c.value for c in ToothCondition]
        if v not in valid_conditions:
            raise ValueError(f"Invalid condition: {v}. Must be one of {valid_conditions}")
        return v


class ToothRecordCreate(BaseModel):
    """Schema for creating a tooth record."""

    tooth_number: int = Field(..., description="FDI tooth number (11-48 or 51-85)")
    general_condition: str = Field(default="healthy")
    surfaces: dict[str, str] = Field(
        default_factory=lambda: {
            "M": "healthy",
            "D": "healthy",
            "O": "healthy",
            "V": "healthy",
            "L": "healthy",
        }
    )
    notes: str | None = None

    @field_validator("tooth_number")
    @classmethod
    def validate_tooth_number(cls, v: int) -> int:
        if not is_valid_tooth_number(v):
            raise ValueError(f"Invalid tooth number: {v}. Must be valid FDI notation.")
        return v

    @field_validator("general_condition")
    @classmethod
    def validate_general_condition(cls, v: str) -> str:
        valid_conditions = [c.value for c in ToothCondition]
        if v not in valid_conditions:
            raise ValueError(f"Invalid condition: {v}. Must be one of {valid_conditions}")
        return v

    @field_validator("surfaces")
    @classmethod
    def validate_surfaces(cls, v: dict[str, str]) -> dict[str, str]:
        valid_conditions = [c.value for c in ToothCondition]
        for surface, condition in v.items():
            if surface not in SURFACES:
                raise ValueError(f"Invalid surface: {surface}")
            if condition not in valid_conditions:
                raise ValueError(f"Invalid condition for surface {surface}: {condition}")
        return v


class ToothRecordUpdate(BaseModel):
    """Schema for updating a tooth record."""

    general_condition: str | None = None
    surface_updates: list[SurfaceUpdate] | None = None
    notes: str | None = None
    # Positional markers
    is_displaced: bool | None = None
    is_rotated: bool | None = None
    displacement_notes: str | None = None

    @field_validator("general_condition")
    @classmethod
    def validate_general_condition(cls, v: str | None) -> str | None:
        if v is None:
            return v
        valid_conditions = [c.value for c in ToothCondition]
        if v not in valid_conditions:
            raise ValueError(f"Invalid condition: {v}. Must be one of {valid_conditions}")
        return v


class BulkToothUpdate(BaseModel):
    """Schema for bulk updating multiple teeth."""

    tooth_number: int
    general_condition: str | None = None
    surface_updates: list[SurfaceUpdate] | None = None
    notes: str | None = None

    @field_validator("tooth_number")
    @classmethod
    def validate_tooth_number(cls, v: int) -> int:
        if not is_valid_tooth_number(v):
            raise ValueError(f"Invalid tooth number: {v}")
        return v


class BulkUpdateRequest(BaseModel):
    """Request schema for bulk tooth updates."""

    updates: list[BulkToothUpdate]


class ToothRecordResponse(BaseModel):
    """Response schema for a tooth record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    patient_id: UUID
    tooth_number: int
    tooth_type: str
    general_condition: str
    surfaces: dict[str, str]
    notes: str | None
    # Positional markers
    is_displaced: bool = False
    is_rotated: bool = False
    displacement_notes: str | None = None
    created_at: datetime
    updated_at: datetime


class HistoricalToothRecordResponse(BaseModel):
    """Response schema for a historical/reconstructed tooth record.

    Used when viewing odontogram at a past date. Does not include IDs
    and timestamps since those are from reconstruction, not database.
    """

    tooth_number: int
    tooth_type: str
    general_condition: str
    surfaces: dict[str, str]
    notes: str | None = None
    is_displaced: bool = False
    is_rotated: bool = False


class HistoricalTreatmentResponse(BaseModel):
    """Response schema for a historical treatment.

    Used when viewing odontogram at a past date.
    """

    id: UUID
    tooth_record_id: UUID
    tooth_number: int
    treatment_type: str
    treatment_category: str
    surfaces: list[str] | None
    status: str
    recorded_at: datetime
    performed_at: datetime | None
    performed_by: UUID | None
    performed_by_name: str | None = None
    budget_item_id: UUID | None
    source_module: str
    notes: str | None
    treatment_group_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class OdontogramResponse(BaseModel):
    """Full odontogram response with all teeth."""

    patient_id: UUID | str
    teeth: list[ToothRecordResponse]
    treatments: list["TreatmentResponse"] = Field(default_factory=list)
    # Metadata for frontend
    condition_colors: dict[str, str] = Field(default_factory=lambda: CONDITION_COLORS)
    available_conditions: list[str] = Field(
        default_factory=lambda: [c.value for c in ToothCondition]
    )
    surfaces: list[str] = Field(default_factory=lambda: SURFACES)


class HistoricalOdontogramResponse(BaseModel):
    """Response for historical odontogram state at a specific date."""

    patient_id: str
    teeth: list[HistoricalToothRecordResponse]
    treatments: list[HistoricalTreatmentResponse] = Field(default_factory=list)
    # Metadata for frontend
    condition_colors: dict[str, str] = Field(default_factory=lambda: CONDITION_COLORS)
    available_conditions: list[str] = Field(
        default_factory=lambda: [c.value for c in ToothCondition]
    )
    surfaces: list[str] = Field(default_factory=lambda: SURFACES)


class OdontogramHistoryResponse(BaseModel):
    """Response schema for history entries."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tooth_number: int
    change_type: str
    surface: str | None
    old_condition: str | None
    new_condition: str | None
    notes: str | None
    changed_by: UUID
    changed_at: datetime


class HistoryEntryWithUser(OdontogramHistoryResponse):
    """History entry with user info."""

    changed_by_name: str | None = None


# ============================================================================
# Treatment Schemas
# ============================================================================


class TreatmentCreate(BaseModel):
    """Schema for creating a tooth treatment."""

    treatment_type: str = Field(..., description="Type of treatment: filling, crown, etc.")
    status: str = Field(
        default=TreatmentStatus.EXISTING.value,
        description="Treatment status: existing, planned",
    )
    surfaces: list[str] | None = Field(
        default=None, description="Affected surfaces for surface treatments (e.g., ['M', 'O'])"
    )
    notes: str | None = None
    # Integration with budget module
    budget_item_id: UUID | None = Field(default=None, description="Associated budget item ID")
    source_module: str = Field(
        default="odontogram", description="Module that created this treatment"
    )

    @field_validator("treatment_type")
    @classmethod
    def validate_treatment_type(cls, v: str) -> str:
        if not is_valid_treatment_type(v):
            valid_types = list(SURFACE_TREATMENTS | WHOLE_TOOTH_TREATMENTS)
            raise ValueError(f"Invalid treatment type: {v}. Must be one of {valid_types}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid_statuses = [s.value for s in TreatmentStatus]
        if v not in valid_statuses:
            raise ValueError(f"Invalid status: {v}. Must be one of {valid_statuses}")
        return v

    @field_validator("surfaces")
    @classmethod
    def validate_surfaces(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        for surface in v:
            if surface not in SURFACES:
                raise ValueError(f"Invalid surface: {surface}. Must be one of {SURFACES}")
        return v


class TreatmentUpdate(BaseModel):
    """Schema for updating a tooth treatment."""

    status: str | None = None
    surfaces: list[str] | None = None
    notes: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        if v is None:
            return v
        valid_statuses = [s.value for s in TreatmentStatus]
        if v not in valid_statuses:
            raise ValueError(f"Invalid status: {v}. Must be one of {valid_statuses}")
        return v

    @field_validator("surfaces")
    @classmethod
    def validate_surfaces(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        for surface in v:
            if surface not in SURFACES:
                raise ValueError(f"Invalid surface: {surface}. Must be one of {SURFACES}")
        return v


class TreatmentPerform(BaseModel):
    """Schema for marking a treatment as performed."""

    notes: str | None = Field(default=None, description="Optional notes when performing treatment")


class TreatmentResponse(BaseModel):
    """Response schema for a tooth treatment."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tooth_record_id: UUID
    tooth_number: int
    treatment_type: str
    treatment_category: str
    surfaces: list[str] | None
    status: str
    recorded_at: datetime
    performed_at: datetime | None
    performed_by: UUID | None
    performed_by_name: str | None = None
    budget_item_id: UUID | None
    source_module: str
    notes: str | None
    treatment_group_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class ToothRecordWithTreatmentsResponse(ToothRecordResponse):
    """Tooth record response including treatments."""

    treatments: list[TreatmentResponse] = Field(default_factory=list)


class TreatmentGroupCreate(BaseModel):
    """Create an atomic multi-tooth treatment group (bridge, splint, etc.)."""

    mode: Literal["bridge", "uniform"] = Field(
        ...,
        description=(
            "bridge: auto-assigns bridge_abutment to first+last tooth and pontic to the middle "
            "ones. uniform: all teeth get the same treatment_type."
        ),
    )
    tooth_numbers: list[int] = Field(..., description="Teeth that form the group (FDI notation)")
    treatment_type: str | None = Field(
        default=None,
        description="Treatment type (required in uniform mode, forbidden in bridge mode)",
    )
    surfaces: list[str] | None = Field(
        default=None, description="Affected surfaces when treatment_type is a surface treatment"
    )
    status: Literal["existing", "planned"] = "planned"
    notes: str | None = None
    catalog_item_id: UUID | None = None
    budget_item_id: UUID | None = None

    @field_validator("tooth_numbers")
    @classmethod
    def validate_tooth_numbers(cls, v: list[int]) -> list[int]:
        for n in v:
            if not is_valid_tooth_number(n):
                raise ValueError(f"Invalid tooth number: {n}")
        if len(v) != len(set(v)):
            raise ValueError("Duplicate tooth numbers not allowed")
        return v

    @field_validator("surfaces")
    @classmethod
    def validate_surfaces(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        for s in v:
            if s not in SURFACES:
                raise ValueError(f"Invalid surface: {s}. Must be one of {SURFACES}")
        return v

    @model_validator(mode="after")
    def validate_mode(self) -> "TreatmentGroupCreate":
        if self.mode == "bridge":
            if len(self.tooth_numbers) < 3:
                raise ValueError("Bridge requires at least 3 teeth")
            if self.treatment_type is not None:
                raise ValueError(
                    "treatment_type must not be set in bridge mode (roles are auto-assigned)"
                )
        else:  # uniform
            if len(self.tooth_numbers) < 2:
                raise ValueError("Uniform group requires at least 2 teeth")
            if not self.treatment_type:
                raise ValueError("treatment_type is required in uniform mode")
            if not is_valid_treatment_type(self.treatment_type):
                raise ValueError(f"Invalid treatment type: {self.treatment_type}")
        return self


class TreatmentGroupPerform(BaseModel):
    """Mark all members of a treatment group as performed."""

    notes: str | None = None


class TreatmentListFilter(BaseModel):
    """Filter parameters for listing treatments."""

    status: str | None = Field(default=None, description="Filter by status")
    treatment_type: str | None = Field(default=None, description="Filter by treatment type")
    tooth_number: int | None = Field(default=None, description="Filter by tooth number")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        if v is None:
            return v
        valid_statuses = [s.value for s in TreatmentStatus]
        if v not in valid_statuses:
            raise ValueError(f"Invalid status: {v}. Must be one of {valid_statuses}")
        return v


# ============================================================================
# Timeline Schemas
# ============================================================================


class TimelineDateEntry(BaseModel):
    """Entry in timeline with date and change count."""

    date: str = Field(..., description="Date in YYYY-MM-DD format")
    change_count: int = Field(..., description="Number of changes on this date")


class TimelineResponse(BaseModel):
    """Response schema for odontogram timeline."""

    dates: list[TimelineDateEntry] = Field(default_factory=list)
    total: int = Field(default=0, description="Total number of distinct dates")


# Rebuild models to resolve forward references
OdontogramResponse.model_rebuild()
