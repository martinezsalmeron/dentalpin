"""Catalog module Pydantic schemas for API request/response."""

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

# ============================================================================
# VAT Type Schemas
# ============================================================================


class VatTypeCreate(BaseModel):
    """Schema for creating a VAT type."""

    names: dict[str, str] = Field(default_factory=dict)  # {"es": "Nombre", "en": "Name"}
    rate: float = Field(default=0.0, ge=0, le=100)
    is_default: bool = False


class VatTypeUpdate(BaseModel):
    """Schema for updating a VAT type."""

    names: dict[str, str] | None = None
    rate: float | None = Field(default=None, ge=0, le=100)
    is_default: bool | None = None
    is_active: bool | None = None


class VatTypeResponse(BaseModel):
    """Schema for VAT type response."""

    id: UUID
    clinic_id: UUID
    names: dict[str, str]
    rate: float
    is_default: bool
    is_active: bool
    is_system: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VatTypeBrief(BaseModel):
    """Brief VAT type info for lists and selects."""

    id: UUID
    names: dict[str, str]
    rate: float
    is_default: bool
    is_active: bool
    is_system: bool

    class Config:
        from_attributes = True


# ============================================================================
# Category Schemas
# ============================================================================


class CategoryCreate(BaseModel):
    """Schema for creating a treatment category."""

    key: str = Field(min_length=1, max_length=50)
    names: dict[str, str] = Field(default_factory=dict)  # {"es": "Nombre", "en": "Name"}
    descriptions: dict[str, str] | None = None
    parent_id: UUID | None = None
    display_order: int = 0
    icon: str | None = None


class CategoryUpdate(BaseModel):
    """Schema for updating a treatment category."""

    key: str | None = Field(default=None, min_length=1, max_length=50)
    names: dict[str, str] | None = None
    descriptions: dict[str, str] | None = None
    parent_id: UUID | None = None
    display_order: int | None = None
    icon: str | None = None
    is_active: bool | None = None


class CategoryResponse(BaseModel):
    """Schema for treatment category response."""

    id: UUID
    clinic_id: UUID
    parent_id: UUID | None
    key: str
    names: dict[str, str]
    descriptions: dict[str, str] | None
    display_order: int
    icon: str | None
    is_active: bool
    is_system: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CategoryTreeResponse(CategoryResponse):
    """Schema for category with nested children (tree structure)."""

    children: list["CategoryTreeResponse"] = []

    class Config:
        from_attributes = True


# ============================================================================
# Odontogram Mapping Schemas
# ============================================================================


class OdontogramMappingCreate(BaseModel):
    """Schema for creating odontogram mapping (usually part of item creation)."""

    odontogram_treatment_type: str = Field(max_length=30)
    visualization_rules: list[str] = Field(default_factory=list)
    visualization_config: dict = Field(default_factory=dict)
    clinical_category: str = Field(max_length=20)


class OdontogramMappingResponse(BaseModel):
    """Schema for odontogram mapping response."""

    id: UUID
    odontogram_treatment_type: str
    visualization_rules: list[str]
    visualization_config: dict
    clinical_category: str

    class Config:
        from_attributes = True


# ============================================================================
# Catalog Item Schemas
# ============================================================================


class CatalogItemCreate(BaseModel):
    """Schema for creating a catalog item."""

    internal_code: str = Field(min_length=1, max_length=50)
    category_id: UUID
    names: dict[str, str] = Field(default_factory=dict)
    descriptions: dict[str, str] | None = None

    # Pricing
    default_price: Decimal | None = Field(default=None, ge=0)
    cost_price: Decimal | None = Field(default=None, ge=0)
    currency: str = Field(default="EUR", max_length=3)

    # Scheduling
    default_duration_minutes: int | None = Field(default=None, ge=0, le=480)  # Max 8 hours
    requires_appointment: bool = True

    # Tax - references VatType by ID (optional, uses clinic default if not provided)
    vat_type_id: UUID | None = None

    # Treatment characteristics
    treatment_scope: Literal["surface", "whole_tooth"] = "whole_tooth"
    is_diagnostic: bool = False
    requires_surfaces: bool = False

    # Material
    material_notes: str | None = None

    # Odontogram mapping (optional)
    odontogram_mapping: OdontogramMappingCreate | None = None


class CatalogItemUpdate(BaseModel):
    """Schema for updating a catalog item."""

    internal_code: str | None = Field(default=None, min_length=1, max_length=50)
    category_id: UUID | None = None
    names: dict[str, str] | None = None
    descriptions: dict[str, str] | None = None

    # Pricing
    default_price: Decimal | None = Field(default=None, ge=0)
    cost_price: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, max_length=3)

    # Scheduling
    default_duration_minutes: int | None = Field(default=None, ge=0, le=480)
    requires_appointment: bool | None = None

    # Tax - references VatType by ID
    vat_type_id: UUID | None = None

    # Treatment characteristics
    treatment_scope: Literal["surface", "whole_tooth"] | None = None
    is_diagnostic: bool | None = None
    requires_surfaces: bool | None = None

    # Material
    material_notes: str | None = None

    # Status
    is_active: bool | None = None

    # Odontogram mapping
    odontogram_mapping: OdontogramMappingCreate | None = None


class CatalogItemResponse(BaseModel):
    """Schema for catalog item response."""

    id: UUID
    clinic_id: UUID
    category_id: UUID
    internal_code: str
    names: dict[str, str]
    descriptions: dict[str, str] | None

    # Pricing
    default_price: Decimal | None
    cost_price: Decimal | None
    currency: str

    # Scheduling
    default_duration_minutes: int | None
    requires_appointment: bool

    # Tax - references VatType
    vat_type_id: UUID | None
    vat_type: VatTypeBrief | None = Field(
        default=None, validation_alias="vat_type_rel"
    )  # Eager loaded

    # Treatment characteristics
    treatment_scope: str
    is_diagnostic: bool
    requires_surfaces: bool

    # Material
    material_notes: str | None

    # Status
    is_active: bool
    is_system: bool
    deleted_at: datetime | None

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Related
    category: CategoryResponse | None = None
    odontogram_mapping: OdontogramMappingResponse | None = None

    class Config:
        from_attributes = True


class CatalogItemBrief(BaseModel):
    """Brief catalog item info for lists."""

    id: UUID
    internal_code: str
    names: dict[str, str]
    default_price: Decimal | None
    is_active: bool

    class Config:
        from_attributes = True


# ============================================================================
# Odontogram Integration Schemas
# ============================================================================


class OdontogramTreatmentResponse(BaseModel):
    """Schema for treatments with odontogram integration.

    Used by the odontogram component to display treatments with proper visualization.
    """

    id: UUID
    internal_code: str
    names: dict[str, str]
    default_price: Decimal | None
    treatment_scope: str
    requires_surfaces: bool
    is_diagnostic: bool

    # Odontogram specific
    odontogram_treatment_type: str
    visualization_rules: list[str]
    visualization_config: dict
    clinical_category: str

    # Category info
    category_key: str
    category_names: dict[str, str]

    class Config:
        from_attributes = True


class OdontogramTreatmentsByCategory(BaseModel):
    """Grouped treatments for TreatmentBar display."""

    category_key: str
    category_names: dict[str, str]
    treatments: list[OdontogramTreatmentResponse]


# ============================================================================
# Search/Filter Schemas
# ============================================================================


class CatalogSearchParams(BaseModel):
    """Search parameters for catalog items."""

    query: str | None = None  # Search in names, codes
    category_id: UUID | None = None
    is_active: bool | None = True
    treatment_scope: Literal["surface", "whole_tooth"] | None = None
    has_odontogram_mapping: bool | None = None
