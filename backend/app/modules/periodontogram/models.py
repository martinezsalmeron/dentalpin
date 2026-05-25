"""Periodontogram models — SEPA snapshots, per-tooth and per-site rows.

A periodontogram is captured as a *snapshot*: a self-contained dated exam.
Each snapshot owns one row per present tooth (``periodontogram_teeth``) and
up to six rows per tooth (``periodontogram_sites``) for the SEPA probing
sites. Snapshots transition draft → closed; closed ones are immutable and
surface in the timeline slider.

No FK to ``odontogram.tooth_records`` — pre-fill happens by *reading*
``OdontogramService`` at draft creation time and persisting denormalised
``tooth_number`` / ``is_implant`` / ``is_present`` flags. Keeps the
uninstall story clean.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.core.auth.models import Clinic, User
    from app.modules.patients.models import Patient


class PeriodontogramSnapshot(Base, TimestampMixin):
    """Dated periodontal exam.

    One ``draft`` allowed per patient (enforced by partial unique index in
    the migration). On close, ``indices`` is frozen as a JSONB blob so
    aggregates (BoP %, PI %, mean CAL, deep-pocket count) can be served
    without recomputing.
    """

    __tablename__ = "periodontogram_snapshots"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id"), nullable=False, index=True
    )
    patient_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True
    )

    status: Mapped[str] = mapped_column(String(10), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recorded_by: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_by: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))

    notes: Mapped[str | None] = mapped_column(Text)
    indices: Mapped[dict | None] = mapped_column(JSONB)

    clinic: Mapped[Clinic] = relationship()
    patient: Mapped[Patient] = relationship()
    recorder: Mapped[User] = relationship(foreign_keys=[recorded_by])
    closer: Mapped[User | None] = relationship(foreign_keys=[closed_by])
    teeth: Mapped[list[PeriodontogramTooth]] = relationship(
        back_populates="snapshot",
        cascade="all, delete-orphan",
    )
    sites: Mapped[list[PeriodontogramSite]] = relationship(
        back_populates="snapshot",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'closed')",
            name="ck_perio_snap_status",
        ),
        CheckConstraint(
            "(status = 'draft' AND closed_at IS NULL AND closed_by IS NULL) "
            "OR (status = 'closed' AND closed_at IS NOT NULL AND closed_by IS NOT NULL)",
            name="ck_perio_snap_closed_pair",
        ),
        Index(
            "ix_perio_snap_patient_status",
            "patient_id",
            "status",
        ),
    )


class PeriodontogramTooth(Base, TimestampMixin):
    """One row per present tooth in a snapshot. SEPA per-tooth metrics."""

    __tablename__ = "periodontogram_teeth"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    snapshot_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("periodontogram_snapshots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    tooth_number: Mapped[int] = mapped_column(Integer, nullable=False)
    is_present: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_implant: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mobility: Mapped[int | None] = mapped_column(Integer)
    prognosis: Mapped[str | None] = mapped_column(String(10))
    furcation_buccal: Mapped[str | None] = mapped_column(String(4))
    furcation_lingual: Mapped[str | None] = mapped_column(String(4))
    keratinized_gingiva_mm: Mapped[int | None] = mapped_column(Integer)

    snapshot: Mapped[PeriodontogramSnapshot] = relationship(back_populates="teeth")
    sites: Mapped[list[PeriodontogramSite]] = relationship(
        back_populates="tooth",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("snapshot_id", "tooth_number", name="uq_perio_tooth_snap"),
        CheckConstraint(
            "tooth_number BETWEEN 11 AND 48 "
            "AND (tooth_number % 10) BETWEEN 1 AND 8 "
            "AND (tooth_number / 10) BETWEEN 1 AND 4",
            name="ck_perio_tooth_fdi",
        ),
        CheckConstraint(
            "mobility IS NULL OR mobility BETWEEN 0 AND 3",
            name="ck_perio_tooth_mobility",
        ),
        CheckConstraint(
            "prognosis IS NULL OR prognosis IN ('good', 'fair', 'poor', 'hopeless')",
            name="ck_perio_tooth_prognosis",
        ),
        CheckConstraint(
            "furcation_buccal IS NULL OR furcation_buccal IN ('0', 'I', 'II', 'III')",
            name="ck_perio_tooth_furcation_b",
        ),
        CheckConstraint(
            "furcation_lingual IS NULL OR furcation_lingual IN ('0', 'I', 'II', 'III')",
            name="ck_perio_tooth_furcation_l",
        ),
        CheckConstraint(
            "keratinized_gingiva_mm IS NULL OR keratinized_gingiva_mm BETWEEN 0 AND 20",
            name="ck_perio_tooth_kg_range",
        ),
    )


class PeriodontogramSite(Base, TimestampMixin):
    """One of six probing sites for a tooth.

    Sites are created lazily — only when the clinician records a value
    there. Bleeding/plaque/suppuration default to false so an explicit
    "no" can be persisted even if probing depth is left empty.
    """

    __tablename__ = "periodontogram_sites"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    snapshot_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("periodontogram_snapshots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tooth_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("periodontogram_teeth.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tooth_number: Mapped[int] = mapped_column(Integer, nullable=False)
    site_code: Mapped[str] = mapped_column(String(2), nullable=False)
    probing_depth_mm: Mapped[int | None] = mapped_column(Integer)
    gingival_margin_mm: Mapped[int | None] = mapped_column(Integer)
    bleeding_on_probing: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    plaque: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    suppuration: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    snapshot: Mapped[PeriodontogramSnapshot] = relationship(back_populates="sites")
    tooth: Mapped[PeriodontogramTooth] = relationship(back_populates="sites")

    __table_args__ = (
        UniqueConstraint(
            "snapshot_id",
            "tooth_number",
            "site_code",
            name="uq_perio_site_snap_tooth_code",
        ),
        CheckConstraint(
            "site_code IN ('MV', 'V', 'DV', 'ML', 'L', 'DL')",
            name="ck_perio_site_code",
        ),
        CheckConstraint(
            "probing_depth_mm IS NULL OR probing_depth_mm BETWEEN 0 AND 15",
            name="ck_perio_site_pd_range",
        ),
        CheckConstraint(
            "gingival_margin_mm IS NULL OR gingival_margin_mm BETWEEN -5 AND 10",
            name="ck_perio_site_gm_range",
        ),
        Index(
            "ix_perio_sites_pd_bop",
            "snapshot_id",
            "probing_depth_mm",
            "bleeding_on_probing",
        ),
    )
