"""Clinical notes + polymorphic note attachments.

Adds ``clinical_notes`` (plan / plan_item) and ``clinical_note_attachments``
(plan / plan_item / appointment_treatment). Visit-level notes continue to
live on ``appointment_treatments.notes`` in the agenda module.

Revision ID: tp_0002
Revises: ag_0003
Create Date: 2026-04-24

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "tp_0002"
down_revision: str | None = "ag_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "clinical_notes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("owner_type", sa.String(length=20), nullable=False),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("author_id", sa.UUID(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"]),
        sa.CheckConstraint(
            "owner_type IN ('plan', 'plan_item')",
            name="ck_clinical_notes_owner_type",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_clinical_notes_owner",
        "clinical_notes",
        ["clinic_id", "owner_type", "owner_id", "created_at"],
        unique=False,
    )
    op.create_index("idx_clinical_notes_author", "clinical_notes", ["author_id"], unique=False)
    op.create_index(
        op.f("ix_clinical_notes_clinic_id"), "clinical_notes", ["clinic_id"], unique=False
    )

    op.create_table(
        "clinical_note_attachments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("owner_type", sa.String(length=30), nullable=False),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column("note_id", sa.UUID(), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["note_id"], ["clinical_notes.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "owner_type IN ('plan', 'plan_item', 'appointment_treatment')",
            name="ck_clinical_note_attachments_owner_type",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "document_id",
            "owner_type",
            "owner_id",
            name="uq_clinical_note_attachments_doc_owner",
        ),
    )
    op.create_index(
        "idx_clinical_note_attachments_owner",
        "clinical_note_attachments",
        ["clinic_id", "owner_type", "owner_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_clinical_note_attachments_clinic_id"),
        "clinical_note_attachments",
        ["clinic_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_clinical_note_attachments_document_id"),
        "clinical_note_attachments",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_clinical_note_attachments_note_id"),
        "clinical_note_attachments",
        ["note_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_clinical_note_attachments_note_id"),
        table_name="clinical_note_attachments",
    )
    op.drop_index(
        op.f("ix_clinical_note_attachments_document_id"),
        table_name="clinical_note_attachments",
    )
    op.drop_index(
        op.f("ix_clinical_note_attachments_clinic_id"),
        table_name="clinical_note_attachments",
    )
    op.drop_index("idx_clinical_note_attachments_owner", table_name="clinical_note_attachments")
    op.drop_table("clinical_note_attachments")

    op.drop_index(op.f("ix_clinical_notes_clinic_id"), table_name="clinical_notes")
    op.drop_index("idx_clinical_notes_author", table_name="clinical_notes")
    op.drop_index("idx_clinical_notes_owner", table_name="clinical_notes")
    op.drop_table("clinical_notes")
