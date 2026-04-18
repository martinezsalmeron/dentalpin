"""Pydantic schemas for odontogram module."""

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .constants import (
    ATOMIC_MULTI_TOOTH_TYPES,
    CONDITION_COLORS,
    SURFACES,
    ToothCondition,
    TreatmentStatus,
    TreatmentType,
    is_valid_tooth_number,
)

# ----------------------------------------------------------------------------
# ToothRecord schemas (state of the tooth itself, independent of treatments)
# ----------------------------------------------------------------------------


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


class ToothRecordUpdate(BaseModel):
    """Schema for updating a tooth record."""

    general_condition: str | None = None
    surface_updates: list[SurfaceUpdate] | None = None
    notes: str | None = None
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
    is_displaced: bool = False
    is_rotated: bool = False
    displacement_notes: str | None = None
    created_at: datetime
    updated_at: datetime


class HistoricalToothRecordResponse(BaseModel):
    """Response schema for a historical/reconstructed tooth record."""

    tooth_number: int
    tooth_type: str
    general_condition: str
    surfaces: dict[str, str]
    notes: str | None = None
    is_displaced: bool = False
    is_rotated: bool = False


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


# ----------------------------------------------------------------------------
# Treatment schemas
# ----------------------------------------------------------------------------


class CatalogItemBrief(BaseModel):
    """Small catalog item shape embedded in TreatmentResponse."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    internal_code: str
    names: dict[str, str]
    default_price: Decimal | None = None
    currency: str = "EUR"


class TreatmentToothResponse(BaseModel):
    """Per-tooth member of a Treatment."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tooth_record_id: UUID
    tooth_number: int
    role: str | None = None
    surfaces: list[str] | None = None


class TreatmentResponse(BaseModel):
    """Response schema for a Treatment including its teeth members."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinical_type: str
    status: str
    catalog_item_id: UUID | None = None
    catalog_item: CatalogItemBrief | None = None
    teeth: list[TreatmentToothResponse] = Field(default_factory=list)

    recorded_at: datetime
    performed_at: datetime | None = None
    performed_by: UUID | None = None
    performed_by_name: str | None = None

    price_snapshot: Decimal | None = None
    currency_snapshot: str | None = None
    duration_snapshot: int | None = None
    vat_rate_snapshot: Decimal | None = None

    budget_item_id: UUID | None = None
    notes: str | None = None
    source_module: str = "odontogram"
    created_at: datetime
    updated_at: datetime


class HistoricalTreatmentResponse(BaseModel):
    """Treatment reconstruction at a past date."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinical_type: str
    status: str
    catalog_item_id: UUID | None = None
    teeth: list[TreatmentToothResponse] = Field(default_factory=list)
    recorded_at: datetime
    performed_at: datetime | None = None
    performed_by: UUID | None = None
    performed_by_name: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class ToothInput(BaseModel):
    """Input for one tooth of a Treatment on creation."""

    tooth_number: int
    role: str | None = None
    surfaces: list[str] | None = None

    @field_validator("tooth_number")
    @classmethod
    def validate_tooth_number(cls, v: int) -> int:
        if not is_valid_tooth_number(v):
            raise ValueError(f"Invalid tooth number: {v}")
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


class TreatmentCreate(BaseModel):
    """Create a Treatment, single- or multi-tooth.

    If catalog_item_id is provided, clinical_type is resolved from the catalog's
    odontogram mapping (server-side) and pricing is snapshotted. Without catalog_item_id,
    clinical_type is required and the treatment is treated as a diagnostic finding
    (no price).
    """

    catalog_item_id: UUID | None = None
    clinical_type: str | None = None
    tooth_numbers: list[int] = Field(default_factory=list)
    teeth: list[ToothInput] | None = None
    """Optional fine-grained input. When given, overrides `tooth_numbers`."""
    surfaces: list[str] | None = None
    """Applied to every tooth without an explicit `surfaces` entry."""
    status: Literal["planned", "performed"] = "planned"
    notes: str | None = None
    budget_item_id: UUID | None = None
    source_module: str = "odontogram"
    # Bridges ignore `clinical_type`/surfaces and auto-assign pillar/pontic roles.
    mode: Literal["single", "bridge", "uniform"] = "single"

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
    def validate_shape(self) -> "TreatmentCreate":
        if not self.teeth and not self.tooth_numbers:
            # Empty teeth are allowed for global treatments (e.g. full-mouth cleaning).
            pass
        if self.teeth:
            nums = [t.tooth_number for t in self.teeth]
            if len(nums) != len(set(nums)):
                raise ValueError("Duplicate tooth numbers in teeth[] not allowed")

        if self.mode == "bridge":
            count = len(self.teeth) if self.teeth else len(self.tooth_numbers)
            if count < 3:
                raise ValueError("Bridge requires at least 3 teeth")

        if self.mode == "uniform":
            count = len(self.teeth) if self.teeth else len(self.tooth_numbers)
            if count < 2:
                raise ValueError("Uniform group requires at least 2 teeth")

        if self.catalog_item_id is None and self.clinical_type is None:
            raise ValueError("Either catalog_item_id or clinical_type is required")

        if self.clinical_type is not None:
            valid_types = [t.value for t in TreatmentType]
            if self.clinical_type not in valid_types:
                raise ValueError(f"Invalid clinical_type: {self.clinical_type}")
            # Atomic multi-tooth types must have enough teeth.
            if self.clinical_type in ATOMIC_MULTI_TOOTH_TYPES:
                count = len(self.teeth) if self.teeth else len(self.tooth_numbers)
                if count < 2:
                    raise ValueError(
                        f"clinical_type={self.clinical_type} requires at least 2 teeth"
                    )
        return self


class TreatmentUpdate(BaseModel):
    """Update a Treatment header.

    `surfaces` replaces the surfaces on every TreatmentTooth of this treatment
    (useful for single-tooth surface treatments like fillings) and triggers a
    recompute of price_snapshot/duration_snapshot from the catalog item.
    """

    status: Literal["planned", "performed"] | None = None
    notes: str | None = None
    surfaces: list[str] | None = None

    @field_validator("surfaces")
    @classmethod
    def validate_surfaces(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        for s in v:
            if s not in SURFACES:
                raise ValueError(f"Invalid surface: {s}. Must be one of {SURFACES}")
        return v


class TreatmentPerform(BaseModel):
    """Mark a Treatment as performed."""

    notes: str | None = None


class TreatmentListFilter(BaseModel):
    """Filter parameters for listing treatments."""

    status: str | None = Field(default=None, description="Filter by status")
    clinical_type: str | None = Field(default=None, description="Filter by clinical type")
    tooth_number: int | None = Field(default=None, description="Filter by any member tooth")
    catalog_item_id: UUID | None = Field(default=None)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        if v is None:
            return v
        valid_statuses = [s.value for s in TreatmentStatus]
        if v not in valid_statuses:
            raise ValueError(f"Invalid status: {v}. Must be one of {valid_statuses}")
        return v


# ----------------------------------------------------------------------------
# Odontogram composite responses
# ----------------------------------------------------------------------------


class OdontogramResponse(BaseModel):
    """Full odontogram response with all teeth and treatments."""

    patient_id: UUID | str
    teeth: list[ToothRecordResponse]
    treatments: list[TreatmentResponse] = Field(default_factory=list)
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
    condition_colors: dict[str, str] = Field(default_factory=lambda: CONDITION_COLORS)
    available_conditions: list[str] = Field(
        default_factory=lambda: [c.value for c in ToothCondition]
    )
    surfaces: list[str] = Field(default_factory=lambda: SURFACES)


class ToothRecordWithTreatmentsResponse(ToothRecordResponse):
    """Tooth record including treatments whose members include this tooth."""

    treatments: list[TreatmentResponse] = Field(default_factory=list)


# ----------------------------------------------------------------------------
# Timeline schemas
# ----------------------------------------------------------------------------


class TimelineDateEntry(BaseModel):
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    change_count: int = Field(..., description="Number of changes on this date")


class TimelineResponse(BaseModel):
    dates: list[TimelineDateEntry] = Field(default_factory=list)
    total: int = Field(default=0)


OdontogramResponse.model_rebuild()
