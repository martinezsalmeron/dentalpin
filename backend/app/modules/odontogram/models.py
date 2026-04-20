"""Odontogram module database models.

Core entities:
- ToothRecord: current state of a tooth (condition, surfaces, positional markers).
- Treatment: a clinical act (single or multi-tooth). May be backed by a catalog item.
- TreatmentTooth: per-tooth member of a Treatment (holds role and surfaces).
- OdontogramHistory: audit log of tooth-state changes.
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
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
    from app.core.auth.models import Clinic, User
    from app.modules.catalog.models import TreatmentCatalogItem
    from app.modules.patients.models import Patient


class ToothRecord(Base, TimestampMixin):
    """Current state of a single tooth for a patient.

    Holds general condition, per-surface conditions and orthodontic positional flags.
    Performed treatments may overlay visualization on top of this state.
    """

    __tablename__ = "tooth_records"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)
    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id"), index=True)
    tooth_number: Mapped[int] = mapped_column(Integer)  # FDI notation: 11-48, 51-85
    tooth_type: Mapped[str] = mapped_column(String(20))  # permanent, deciduous
    general_condition: Mapped[str] = mapped_column(String(30), default="healthy")
    surfaces: Mapped[dict] = mapped_column(JSONB, default=dict)
    notes: Mapped[str | None] = mapped_column(Text)

    # Positional markers (orthodontic)
    is_displaced: Mapped[bool] = mapped_column(Boolean, default=False)
    is_rotated: Mapped[bool] = mapped_column(Boolean, default=False)
    displacement_notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    clinic: Mapped["Clinic"] = relationship()
    patient: Mapped["Patient"] = relationship()
    treatment_teeth: Mapped[list["TreatmentTooth"]] = relationship(
        back_populates="tooth_record", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("patient_id", "tooth_number", name="uq_patient_tooth"),
        Index("idx_tooth_records_patient", "patient_id"),
        Index("idx_tooth_records_clinic_patient", "clinic_id", "patient_id"),
    )


class Treatment(Base, TimestampMixin):
    """A clinical treatment act. Can affect 1 or N teeth.

    One Treatment == one clinical decision. A bridge, a splint or N crowns created
    together are all single Treatment rows with N children in TreatmentTooth.
    """

    __tablename__ = "treatments"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)
    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id"), index=True)

    # Clinical type (drives visualization rules). Required.
    # Examples: bridge, crown, filling_composite, splint, caries, pulpitis, ...
    clinical_type: Mapped[str] = mapped_column(String(30))

    # Scope determines how the treatment relates to teeth:
    #   tooth         → 1 TreatmentTooth, surfaces optional (inside tooth row)
    #   multi_tooth   → N TreatmentTooth with optional role (pillar/pontic/cantilever)
    #   global_mouth  → 0 TreatmentTooth (e.g. cleaning, whitening)
    #   global_arch   → 0 TreatmentTooth, `arch` required
    scope: Mapped[str] = mapped_column(String(20), default="tooth")

    # Arch (only meaningful when scope == 'global_arch').
    arch: Mapped[str | None] = mapped_column(String(10))

    # Link to catalog item. NULL is valid only for pre-existing diagnostic conditions
    # without a known catalog entry (caries, missing, pre-existing prosthesis).
    catalog_item_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("treatment_catalog_items.id"), index=True, default=None
    )

    # Status
    status: Mapped[str] = mapped_column(String(20))  # planned | performed

    # Timestamps
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    performed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    performed_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))

    # Pricing snapshots (frozen at creation; decouples history from catalog edits).
    price_snapshot: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    currency_snapshot: Mapped[str | None] = mapped_column(String(3))
    duration_snapshot: Mapped[int | None] = mapped_column(Integer)
    vat_rate_snapshot: Mapped[float | None] = mapped_column(Numeric(5, 2))

    # Budget / invoicing integration
    budget_item_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True))

    # Free-form clinical notes
    notes: Mapped[str | None] = mapped_column(Text)
    source_module: Mapped[str] = mapped_column(String(30), default="odontogram")

    # Soft delete
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    clinic: Mapped["Clinic"] = relationship()
    patient: Mapped["Patient"] = relationship()
    catalog_item: Mapped["TreatmentCatalogItem | None"] = relationship()
    performer: Mapped["User | None"] = relationship(foreign_keys=[performed_by])
    teeth: Mapped[list["TreatmentTooth"]] = relationship(
        back_populates="treatment",
        cascade="all, delete-orphan",
        order_by="TreatmentTooth.tooth_number",
    )

    __table_args__ = (
        Index("idx_treatments_patient", "patient_id"),
        Index("idx_treatments_status", "patient_id", "status"),
        Index("idx_treatments_catalog", "catalog_item_id"),
        Index("idx_treatments_budget", "budget_item_id"),
        CheckConstraint(
            "scope IN ('tooth', 'multi_tooth', 'global_mouth', 'global_arch')",
            name="ck_treatments_scope",
        ),
        CheckConstraint(
            "(scope = 'global_arch' AND arch IS NOT NULL) OR "
            "(scope <> 'global_arch' AND arch IS NULL)",
            name="ck_treatments_arch_matches_scope",
        ),
        CheckConstraint(
            "arch IS NULL OR arch IN ('upper', 'lower')",
            name="ck_treatments_arch_value",
        ),
    )


class TreatmentTooth(Base, TimestampMixin):
    """Per-tooth member of a Treatment.

    Holds tooth-specific data (role inside a group, affected surfaces).
    A single-tooth treatment has exactly one TreatmentTooth row.
    """

    __tablename__ = "treatment_teeth"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    treatment_id: Mapped[UUID] = mapped_column(
        ForeignKey("treatments.id", ondelete="CASCADE"), index=True
    )
    tooth_record_id: Mapped[UUID] = mapped_column(ForeignKey("tooth_records.id"), index=True)
    tooth_number: Mapped[int] = mapped_column(Integer)  # denormalized for queries

    # Role inside the treatment (bridges use pillar/pontic; otherwise NULL).
    role: Mapped[str | None] = mapped_column(String(20))

    # For surface treatments (fillings, sealants, veneers).
    surfaces: Mapped[list | None] = mapped_column(JSONB)

    # Relationships
    treatment: Mapped["Treatment"] = relationship(back_populates="teeth")
    tooth_record: Mapped["ToothRecord"] = relationship(back_populates="treatment_teeth")

    __table_args__ = (
        UniqueConstraint("treatment_id", "tooth_number", name="uq_treatment_tooth"),
        Index("idx_treatment_teeth_treatment", "treatment_id"),
        Index("idx_treatment_teeth_tooth_record", "tooth_record_id"),
    )


class OdontogramHistory(Base):
    """Audit log for tooth-state changes."""

    __tablename__ = "odontogram_history"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)
    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id"), index=True)
    tooth_number: Mapped[int] = mapped_column(Integer)
    change_type: Mapped[str] = mapped_column(String(30))
    surface: Mapped[str | None] = mapped_column(String(1))
    old_condition: Mapped[str | None] = mapped_column(String(30))
    new_condition: Mapped[str | None] = mapped_column(String(30))
    notes: Mapped[str | None] = mapped_column(Text)
    changed_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Relationships
    clinic: Mapped["Clinic"] = relationship()
    patient: Mapped["Patient"] = relationship()
    user: Mapped["User"] = relationship()

    __table_args__ = (
        Index("idx_odontogram_history_patient", "patient_id"),
        Index("idx_odontogram_history_tooth", "patient_id", "tooth_number"),
    )
