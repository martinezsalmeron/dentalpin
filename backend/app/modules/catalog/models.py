"""Catalog module database models."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.core.auth.models import Clinic


class VatType(Base, TimestampMixin):
    """VAT type configuration for treatments.

    Centralizes VAT definitions so treatments reference a VAT type by ID
    instead of storing type/rate separately. Prevents inconsistent combinations.
    """

    __tablename__ = "vat_types"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)

    # Localized names (JSONB for multi-language support)
    names: Mapped[dict] = mapped_column(JSONB, default=dict)  # {"es": "Exento", "en": "Exempt"}

    # VAT rate percentage (0-100)
    rate: Mapped[float] = mapped_column(Float, default=0.0)

    # Default flag - only one per clinic should be default
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)  # System-seeded, cannot delete

    # Relationships
    clinic: Mapped["Clinic"] = relationship()
    catalog_items: Mapped[list["TreatmentCatalogItem"]] = relationship(
        back_populates="vat_type_rel"
    )

    __table_args__ = (
        Index("idx_vat_types_clinic", "clinic_id"),
        Index("idx_vat_types_default", "clinic_id", "is_default"),
    )


class TreatmentCategory(Base, TimestampMixin):
    """Hierarchical category for organizing treatments.

    Categories form a tree structure for grouping related treatments.
    Examples: Diagnóstico, Restauradora, Cirugía, Endodoncia, Ortodoncia
    """

    __tablename__ = "treatment_categories"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)

    # Hierarchy
    parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("treatment_categories.id"), index=True, default=None
    )

    # Identification
    key: Mapped[str] = mapped_column(String(50))  # e.g., "diagnostico", "restauradora"

    # Localized content (JSONB for multi-language support)
    names: Mapped[dict] = mapped_column(
        JSONB, default=dict
    )  # {"es": "Diagnóstico", "en": "Diagnostic"}
    descriptions: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    # Display
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    icon: Mapped[str | None] = mapped_column(String(50))  # Icon name/class

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)  # System-seeded, cannot delete

    # Relationships
    clinic: Mapped["Clinic"] = relationship()
    parent: Mapped["TreatmentCategory | None"] = relationship(
        remote_side="TreatmentCategory.id", foreign_keys=[parent_id]
    )
    items: Mapped[list["TreatmentCatalogItem"]] = relationship(
        back_populates="category", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("clinic_id", "key", name="uq_category_clinic_key"),
        Index("idx_treatment_categories_clinic", "clinic_id"),
        Index("idx_treatment_categories_parent", "parent_id"),
    )


class TreatmentCatalogItem(Base, TimestampMixin):
    """Core treatment definition in the catalog.

    Represents a single treatment type that can be:
    - Applied to teeth in the odontogram
    - Added to budgets/invoices
    - Associated with appointments

    MVP includes single default price. Phase 2 adds multiple price lists.
    """

    __tablename__ = "treatment_catalog_items"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)
    category_id: Mapped[UUID] = mapped_column(ForeignKey("treatment_categories.id"), index=True)

    # Identification
    internal_code: Mapped[str] = mapped_column(String(50))  # e.g., "CORONA-01", "ENDO-01"

    # Localized content
    names: Mapped[dict] = mapped_column(JSONB, default=dict)  # {"es": "Corona", "en": "Crown"}
    descriptions: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    # Pricing (MVP: single default price)
    default_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    cost_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))  # For margin calculation
    currency: Mapped[str] = mapped_column(String(3), default="EUR")  # ISO 4217

    # Scheduling
    default_duration_minutes: Mapped[int | None] = mapped_column(Integer)
    requires_appointment: Mapped[bool] = mapped_column(Boolean, default=True)

    # Tax configuration - references VatType
    vat_type_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("vat_types.id"), index=True, default=None
    )

    # Legacy fields (kept for backward compatibility during migration, will be removed later)
    vat_type: Mapped[str | None] = mapped_column(
        String(20), default=None
    )  # exempt, reduced, standard
    vat_rate: Mapped[float | None] = mapped_column(Float, default=None)  # 0, 10, 21

    # Treatment characteristics
    treatment_scope: Mapped[str] = mapped_column(
        String(20), default="whole_tooth"
    )  # "surface" or "whole_tooth"
    is_diagnostic: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_surfaces: Mapped[bool] = mapped_column(Boolean, default=False)

    # Billing configuration
    billing_mode: Mapped[str] = mapped_column(
        String(20), default="on_completion"
    )  # on_completion, on_acceptance, manual

    # Material reference (placeholder for future inventory module)
    material_notes: Mapped[str | None] = mapped_column(Text)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)  # System-seeded item
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    # Relationships
    clinic: Mapped["Clinic"] = relationship()
    category: Mapped["TreatmentCategory"] = relationship(back_populates="items")
    vat_type_rel: Mapped["VatType | None"] = relationship(back_populates="catalog_items")
    odontogram_mapping: Mapped["TreatmentOdontogramMapping | None"] = relationship(
        back_populates="catalog_item", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("clinic_id", "internal_code", name="uq_catalog_item_clinic_code"),
        Index("idx_catalog_items_clinic", "clinic_id"),
        Index("idx_catalog_items_category", "category_id"),
        Index("idx_catalog_items_active", "clinic_id", "is_active"),
        Index("idx_catalog_items_vat_type", "vat_type_id"),
    )


class TreatmentOdontogramMapping(Base, TimestampMixin):
    """Bridge between catalog items and odontogram visualization.

    Maps a catalog item to an existing odontogram treatment type,
    preserving the visualization rules from the constants file.
    """

    __tablename__ = "treatment_odontogram_mappings"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)
    catalog_item_id: Mapped[UUID] = mapped_column(
        ForeignKey("treatment_catalog_items.id", ondelete="CASCADE"), unique=True
    )

    # Odontogram integration
    odontogram_treatment_type: Mapped[str] = mapped_column(
        String(30)
    )  # Maps to TreatmentType enum: filling_composite, crown, etc.

    # Visualization configuration
    visualization_rules: Mapped[list] = mapped_column(
        JSONB, default=list
    )  # ["pulp_fill", "lateral_icon", etc.]
    visualization_config: Mapped[dict] = mapped_column(
        JSONB, default=dict
    )  # Colors, patterns, custom config

    # Clinical category for TreatmentBar grouping
    clinical_category: Mapped[str] = mapped_column(
        String(20)
    )  # diagnostico, restauradora, cirugia, endodoncia, ortodoncia

    # Relationships
    clinic: Mapped["Clinic"] = relationship()
    catalog_item: Mapped["TreatmentCatalogItem"] = relationship(back_populates="odontogram_mapping")

    __table_args__ = (
        Index("idx_odontogram_mapping_clinic", "clinic_id"),
        Index("idx_odontogram_mapping_type", "odontogram_treatment_type"),
    )
