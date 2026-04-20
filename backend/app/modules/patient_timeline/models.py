"""Patient timeline model.

Denormalized audit log of patient-scoped events. Moved from
``app.modules.clinical.models`` in Fase B.3. The backing table
(``patient_timeline``) keeps its name so cross-module FKs continue
to resolve.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.core.auth.models import Clinic, User
    from app.modules.patients.models import Patient


class PatientTimeline(Base):
    """Denormalized timeline of patient events for efficient retrieval."""

    __tablename__ = "patient_timeline"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id"), index=True)
    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(50))
    event_category: Mapped[str] = mapped_column(String(30))
    source_table: Mapped[str] = mapped_column(String(50))
    source_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    event_data: Mapped[dict | None] = mapped_column(JSONB)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))

    clinic: Mapped[Clinic] = relationship()
    patient: Mapped[Patient] = relationship(back_populates="timeline_entries")
    created_by_user: Mapped[User | None] = relationship()

    __table_args__ = (
        Index("idx_timeline_patient_date", "patient_id", "occurred_at"),
        Index("idx_timeline_clinic_patient", "clinic_id", "patient_id"),
    )
