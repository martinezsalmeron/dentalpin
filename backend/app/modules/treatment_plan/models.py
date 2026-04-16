"""Treatment plan module database models."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.core.auth.models import Clinic, User
    from app.modules.budget.models import Budget
    from app.modules.catalog.models import TreatmentCatalogItem
    from app.modules.clinical.models import Patient
    from app.modules.media.models import Document
    from app.modules.odontogram.models import ToothTreatment


class TreatmentPlan(Base, TimestampMixin):
    """Treatment plan that groups treatments for a patient.

    Orchestrates the patient workflow by linking treatments from the odontogram
    with budgets and appointments. Communicates with other modules via event bus.
    """

    __tablename__ = "treatment_plans"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)
    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id"), index=True)

    # Identification
    plan_number: Mapped[str] = mapped_column(String(50))  # PLAN-2024-0001
    title: Mapped[str | None] = mapped_column(String(200))

    # Status workflow: draft, active, completed, archived, cancelled
    status: Mapped[str] = mapped_column(String(20), default="draft")

    # Budget integration (one-to-one)
    budget_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("budgets.id"), unique=True, index=True
    )

    # Assignments
    assigned_professional_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))

    # Clinical notes
    diagnosis_notes: Mapped[str | None] = mapped_column(Text)
    internal_notes: Mapped[str | None] = mapped_column(Text)

    # Soft delete
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    clinic: Mapped["Clinic"] = relationship(foreign_keys=[clinic_id])
    patient: Mapped["Patient"] = relationship()
    budget: Mapped["Budget | None"] = relationship()
    assigned_professional: Mapped["User | None"] = relationship(
        foreign_keys=[assigned_professional_id]
    )
    creator: Mapped["User"] = relationship(foreign_keys=[created_by])
    items: Mapped[list["PlannedTreatmentItem"]] = relationship(
        back_populates="treatment_plan",
        cascade="all, delete-orphan",
        order_by="PlannedTreatmentItem.sequence_order",
    )

    __table_args__ = (
        UniqueConstraint("clinic_id", "plan_number", name="uq_treatment_plan_number"),
        Index("idx_treatment_plans_patient", "patient_id"),
        Index("idx_treatment_plans_status", "clinic_id", "status"),
        Index("idx_treatment_plans_budget", "budget_id"),
    )


class PlannedTreatmentItem(Base, TimestampMixin):
    """Individual treatment within a plan.

    Can reference a ToothTreatment (for tooth-specific treatments) or
    be a global treatment (without a specific tooth).
    """

    __tablename__ = "planned_treatment_items"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)
    treatment_plan_id: Mapped[UUID] = mapped_column(
        ForeignKey("treatment_plans.id", ondelete="CASCADE"), index=True
    )

    # Reference to ToothTreatment (if tooth-specific)
    tooth_treatment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("tooth_treatments.id"), index=True
    )

    # For global treatments (without a specific tooth)
    catalog_item_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("treatment_catalog_items.id"), index=True
    )
    is_global: Mapped[bool] = mapped_column(Boolean, default=False)

    # Ordering and status
    sequence_order: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending|completed|cancelled

    # Completion tracking
    completed_without_appointment: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))

    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    clinic: Mapped["Clinic"] = relationship()
    treatment_plan: Mapped["TreatmentPlan"] = relationship(back_populates="items")
    tooth_treatment: Mapped["ToothTreatment | None"] = relationship()
    catalog_item: Mapped["TreatmentCatalogItem | None"] = relationship()
    completer: Mapped["User | None"] = relationship(foreign_keys=[completed_by])
    media: Mapped[list["TreatmentMedia"]] = relationship(
        back_populates="planned_item", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_planned_items_plan", "treatment_plan_id"),
        Index("idx_planned_items_tooth", "tooth_treatment_id"),
        Index("idx_planned_items_status", "treatment_plan_id", "status"),
    )


class TreatmentMedia(Base, TimestampMixin):
    """Images associated with a planned treatment item.

    Links to the media module's Document model for actual file storage.
    """

    __tablename__ = "treatment_media"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)
    planned_treatment_item_id: Mapped[UUID] = mapped_column(
        ForeignKey("planned_treatment_items.id", ondelete="CASCADE"), index=True
    )
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )

    # Media classification
    media_type: Mapped[str] = mapped_column(String(20))  # before|after|xray|reference
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    clinic: Mapped["Clinic"] = relationship()
    planned_item: Mapped["PlannedTreatmentItem"] = relationship(back_populates="media")
    document: Mapped["Document"] = relationship()

    __table_args__ = (
        Index("idx_treatment_media_item", "planned_treatment_item_id"),
        Index("idx_treatment_media_document", "document_id"),
    )
