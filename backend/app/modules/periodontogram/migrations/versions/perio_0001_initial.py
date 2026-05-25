"""periodontogram module — initial schema.

Revision ID: perio_0001
Revises: 0001
Create Date: 2026-05-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "perio_0001"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = ("periodontogram",)
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "periodontogram_snapshots",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recorded_by", sa.UUID(), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_by", sa.UUID(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("indices", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('draft', 'closed')", name="ck_perio_snap_status"),
        sa.CheckConstraint(
            "(status = 'draft' AND closed_at IS NULL AND closed_by IS NULL) "
            "OR (status = 'closed' AND closed_at IS NOT NULL AND closed_by IS NOT NULL)",
            name="ck_perio_snap_closed_pair",
        ),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
        sa.ForeignKeyConstraint(["recorded_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["closed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_periodontogram_snapshots_clinic_id"),
        "periodontogram_snapshots",
        ["clinic_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_periodontogram_snapshots_patient_id"),
        "periodontogram_snapshots",
        ["patient_id"],
        unique=False,
    )
    op.create_index(
        "ix_perio_snap_patient_status",
        "periodontogram_snapshots",
        ["patient_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_perio_snap_patient_closed_at",
        "periodontogram_snapshots",
        ["patient_id", sa.text("closed_at DESC")],
        unique=False,
        postgresql_where=sa.text("status = 'closed'"),
    )
    op.create_index(
        "uq_perio_snap_one_draft_per_patient",
        "periodontogram_snapshots",
        ["patient_id"],
        unique=True,
        postgresql_where=sa.text("status = 'draft'"),
    )

    op.create_table(
        "periodontogram_teeth",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("snapshot_id", sa.UUID(), nullable=False),
        sa.Column("tooth_number", sa.Integer(), nullable=False),
        sa.Column("is_present", sa.Boolean(), nullable=False),
        sa.Column("is_implant", sa.Boolean(), nullable=False),
        sa.Column("mobility", sa.Integer(), nullable=True),
        sa.Column("prognosis", sa.String(length=10), nullable=True),
        sa.Column("furcation_buccal", sa.String(length=4), nullable=True),
        sa.Column("furcation_lingual", sa.String(length=4), nullable=True),
        sa.Column("keratinized_gingiva_mm", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "tooth_number BETWEEN 11 AND 48 "
            "AND (tooth_number % 10) BETWEEN 1 AND 8 "
            "AND (tooth_number / 10) BETWEEN 1 AND 4",
            name="ck_perio_tooth_fdi",
        ),
        sa.CheckConstraint(
            "mobility IS NULL OR mobility BETWEEN 0 AND 3",
            name="ck_perio_tooth_mobility",
        ),
        sa.CheckConstraint(
            "prognosis IS NULL OR prognosis IN ('good', 'fair', 'poor', 'hopeless')",
            name="ck_perio_tooth_prognosis",
        ),
        sa.CheckConstraint(
            "furcation_buccal IS NULL OR furcation_buccal IN ('0', 'I', 'II', 'III')",
            name="ck_perio_tooth_furcation_b",
        ),
        sa.CheckConstraint(
            "furcation_lingual IS NULL OR furcation_lingual IN ('0', 'I', 'II', 'III')",
            name="ck_perio_tooth_furcation_l",
        ),
        sa.CheckConstraint(
            "keratinized_gingiva_mm IS NULL OR keratinized_gingiva_mm BETWEEN 0 AND 20",
            name="ck_perio_tooth_kg_range",
        ),
        sa.ForeignKeyConstraint(
            ["snapshot_id"],
            ["periodontogram_snapshots.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("snapshot_id", "tooth_number", name="uq_perio_tooth_snap"),
    )
    op.create_index(
        op.f("ix_periodontogram_teeth_snapshot_id"),
        "periodontogram_teeth",
        ["snapshot_id"],
        unique=False,
    )

    op.create_table(
        "periodontogram_sites",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("snapshot_id", sa.UUID(), nullable=False),
        sa.Column("tooth_id", sa.UUID(), nullable=False),
        sa.Column("tooth_number", sa.Integer(), nullable=False),
        sa.Column("site_code", sa.String(length=2), nullable=False),
        sa.Column("probing_depth_mm", sa.Integer(), nullable=True),
        sa.Column("gingival_margin_mm", sa.Integer(), nullable=True),
        sa.Column("bleeding_on_probing", sa.Boolean(), nullable=False),
        sa.Column("plaque", sa.Boolean(), nullable=False),
        sa.Column("suppuration", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "site_code IN ('MV', 'V', 'DV', 'ML', 'L', 'DL')",
            name="ck_perio_site_code",
        ),
        sa.CheckConstraint(
            "probing_depth_mm IS NULL OR probing_depth_mm BETWEEN 0 AND 15",
            name="ck_perio_site_pd_range",
        ),
        sa.CheckConstraint(
            "gingival_margin_mm IS NULL OR gingival_margin_mm BETWEEN -5 AND 10",
            name="ck_perio_site_gm_range",
        ),
        sa.ForeignKeyConstraint(
            ["snapshot_id"],
            ["periodontogram_snapshots.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tooth_id"],
            ["periodontogram_teeth.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "snapshot_id",
            "tooth_number",
            "site_code",
            name="uq_perio_site_snap_tooth_code",
        ),
    )
    op.create_index(
        op.f("ix_periodontogram_sites_snapshot_id"),
        "periodontogram_sites",
        ["snapshot_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_periodontogram_sites_tooth_id"),
        "periodontogram_sites",
        ["tooth_id"],
        unique=False,
    )
    op.create_index(
        "ix_perio_sites_pd_bop",
        "periodontogram_sites",
        ["snapshot_id", "probing_depth_mm", "bleeding_on_probing"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_perio_sites_pd_bop", table_name="periodontogram_sites")
    op.drop_index(
        op.f("ix_periodontogram_sites_tooth_id"),
        table_name="periodontogram_sites",
    )
    op.drop_index(
        op.f("ix_periodontogram_sites_snapshot_id"),
        table_name="periodontogram_sites",
    )
    op.drop_table("periodontogram_sites")

    op.drop_index(
        op.f("ix_periodontogram_teeth_snapshot_id"),
        table_name="periodontogram_teeth",
    )
    op.drop_table("periodontogram_teeth")

    op.drop_index(
        "uq_perio_snap_one_draft_per_patient",
        table_name="periodontogram_snapshots",
    )
    op.drop_index(
        "ix_perio_snap_patient_closed_at",
        table_name="periodontogram_snapshots",
    )
    op.drop_index(
        "ix_perio_snap_patient_status",
        table_name="periodontogram_snapshots",
    )
    op.drop_index(
        op.f("ix_periodontogram_snapshots_patient_id"),
        table_name="periodontogram_snapshots",
    )
    op.drop_index(
        op.f("ix_periodontogram_snapshots_clinic_id"),
        table_name="periodontogram_snapshots",
    )
    op.drop_table("periodontogram_snapshots")
