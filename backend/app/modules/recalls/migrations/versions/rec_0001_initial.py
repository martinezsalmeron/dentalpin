"""recalls: initial schema.

Tables:
    - ``recalls`` — patient call-back rows.
    - ``recall_contact_attempts`` — append-only attempt log.
    - ``recall_settings`` — per-clinic configuration.

Lives on its own Alembic branch (``recalls``) per ADR 0002.

Revision ID: rec_0001
Revises:
Create Date: 2026-05-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "rec_0001"
# Chain off the foundational core revision that creates ``clinics`` +
# ``users``. The cross-branch FKs to ``patients`` and ``appointments``
# are declared via ``depends_on`` so those tables exist regardless of
# branch ordering when starting from a clean DB.
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = ("recalls",)
depends_on: str | Sequence[str] | None = ("pat_0001", "ag_0001")


def upgrade() -> None:
    op.create_table(
        "recalls",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("due_month", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("reason", sa.String(length=40), nullable=False),
        sa.Column("reason_note", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("recommended_by", sa.UUID(), nullable=True),
        sa.Column("assigned_professional_id", sa.UUID(), nullable=True),
        sa.Column("last_contact_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("contact_attempt_count", sa.Integer(), nullable=False),
        sa.Column("linked_appointment_id", sa.UUID(), nullable=True),
        sa.Column("linked_treatment_id", sa.UUID(), nullable=True),
        sa.Column("linked_treatment_category_key", sa.String(length=80), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
        sa.ForeignKeyConstraint(["recommended_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["assigned_professional_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["linked_appointment_id"], ["appointments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_recalls_clinic_id"), "recalls", ["clinic_id"])
    op.create_index(op.f("ix_recalls_patient_id"), "recalls", ["patient_id"])
    op.create_index(op.f("ix_recalls_due_month"), "recalls", ["due_month"])
    op.create_index(op.f("ix_recalls_status"), "recalls", ["status"])
    op.create_index(
        "ix_recalls_clinic_due_month_status",
        "recalls",
        ["clinic_id", "due_month", "status"],
    )
    op.create_index(
        "ix_recalls_clinic_patient_reason_status",
        "recalls",
        ["clinic_id", "patient_id", "reason", "status"],
    )

    op.create_table(
        "recall_contact_attempts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("recall_id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column(
            "attempted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("attempted_by", sa.UUID(), nullable=False),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column("outcome", sa.String(length=30), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["recall_id"], ["recalls.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["attempted_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_recall_contact_attempts_recall_id"),
        "recall_contact_attempts",
        ["recall_id"],
    )
    op.create_index(
        op.f("ix_recall_contact_attempts_clinic_id"),
        "recall_contact_attempts",
        ["clinic_id"],
    )

    op.create_table(
        "recall_settings",
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column(
            "reason_intervals",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "category_to_reason",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("auto_suggest_on_treatment_completed", sa.Boolean(), nullable=False),
        sa.Column("auto_link_on_appointment_scheduled", sa.Boolean(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.PrimaryKeyConstraint("clinic_id"),
    )


def downgrade() -> None:
    op.drop_table("recall_settings")
    op.drop_index(
        op.f("ix_recall_contact_attempts_clinic_id"),
        table_name="recall_contact_attempts",
    )
    op.drop_index(
        op.f("ix_recall_contact_attempts_recall_id"),
        table_name="recall_contact_attempts",
    )
    op.drop_table("recall_contact_attempts")
    op.drop_index("ix_recalls_clinic_patient_reason_status", table_name="recalls")
    op.drop_index("ix_recalls_clinic_due_month_status", table_name="recalls")
    op.drop_index(op.f("ix_recalls_status"), table_name="recalls")
    op.drop_index(op.f("ix_recalls_due_month"), table_name="recalls")
    op.drop_index(op.f("ix_recalls_patient_id"), table_name="recalls")
    op.drop_index(op.f("ix_recalls_clinic_id"), table_name="recalls")
    op.drop_table("recalls")
