"""Add budget module tables.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2024-04-11

Tables created:
- budgets: Main budget entity for dental treatment quotes
- budget_items: Individual line items in a budget
- budget_signatures: Digital signature records for budget acceptance
- budget_history: Audit log for budget changes
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: str | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create budgets table
    op.create_table(
        "budgets",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        # Identification
        sa.Column("budget_number", sa.String(length=50), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("parent_budget_id", sa.UUID(), nullable=True),
        # Status
        sa.Column("status", sa.String(length=30), nullable=False, server_default="'draft'"),
        # Validity
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_until", sa.Date(), nullable=True),
        # Assignments
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column("assigned_professional_id", sa.UUID(), nullable=True),
        # Global discount
        sa.Column("global_discount_type", sa.String(length=20), nullable=True),
        sa.Column("global_discount_value", sa.Numeric(precision=10, scale=2), nullable=True),
        # Totals
        sa.Column(
            "subtotal", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0.00"
        ),
        sa.Column(
            "total_discount",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "total_tax", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0.00"
        ),
        sa.Column(
            "total", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0.00"
        ),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="'EUR'"),
        # Notes
        sa.Column("internal_notes", sa.Text(), nullable=True),
        sa.Column("patient_notes", sa.Text(), nullable=True),
        # Future integrations
        sa.Column("insurance_estimate", sa.Numeric(precision=12, scale=2), nullable=True),
        # Soft delete
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        # Constraints
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["assigned_professional_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["parent_budget_id"], ["budgets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "clinic_id", "budget_number", "version", name="uq_budget_clinic_number_version"
        ),
    )
    op.create_index("idx_budgets_clinic", "budgets", ["clinic_id"], unique=False)
    op.create_index(
        "idx_budgets_clinic_patient", "budgets", ["clinic_id", "patient_id"], unique=False
    )
    op.create_index("idx_budgets_clinic_status", "budgets", ["clinic_id", "status"], unique=False)
    op.create_index("idx_budgets_valid_until", "budgets", ["valid_until"], unique=False)
    op.create_index("idx_budgets_parent", "budgets", ["parent_budget_id"], unique=False)

    # Create budget_items table
    op.create_table(
        "budget_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("budget_id", sa.UUID(), nullable=False),
        # Catalog reference
        sa.Column("catalog_item_id", sa.UUID(), nullable=False),
        # Snapshotted pricing
        sa.Column("unit_price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        # Line discount
        sa.Column("discount_type", sa.String(length=20), nullable=True),
        sa.Column("discount_value", sa.Numeric(precision=10, scale=2), nullable=True),
        # VAT (snapshotted)
        sa.Column("vat_type_id", sa.UUID(), nullable=True),
        sa.Column("vat_rate", sa.Float(), nullable=False, server_default="0.0"),
        # Calculated line totals
        sa.Column(
            "line_subtotal",
            sa.Numeric(precision=10, scale=2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "line_discount",
            sa.Numeric(precision=10, scale=2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "line_tax", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0.00"
        ),
        sa.Column(
            "line_total", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0.00"
        ),
        # Dental specifics
        sa.Column("tooth_number", sa.Integer(), nullable=True),
        sa.Column("surfaces", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # Odontogram integration
        sa.Column("tooth_treatment_id", sa.UUID(), nullable=True),
        # Item status
        sa.Column("item_status", sa.String(length=20), nullable=False, server_default="'pending'"),
        # Status timestamps
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("treatment_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("treatment_completed_at", sa.DateTime(timezone=True), nullable=True),
        # Treatment tracking
        sa.Column("performed_by", sa.UUID(), nullable=True),
        # Display
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        # Constraints
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["budget_id"], ["budgets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["catalog_item_id"], ["treatment_catalog_items.id"]),
        sa.ForeignKeyConstraint(["vat_type_id"], ["vat_types.id"]),
        sa.ForeignKeyConstraint(["tooth_treatment_id"], ["tooth_treatments.id"]),
        sa.ForeignKeyConstraint(["performed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_budget_items_budget", "budget_items", ["budget_id"], unique=False)
    op.create_index("idx_budget_items_catalog", "budget_items", ["catalog_item_id"], unique=False)
    op.create_index(
        "idx_budget_items_status", "budget_items", ["budget_id", "item_status"], unique=False
    )
    op.create_index(
        "idx_budget_items_tooth", "budget_items", ["budget_id", "tooth_number"], unique=False
    )
    op.create_index(
        "idx_budget_items_tooth_treatment", "budget_items", ["tooth_treatment_id"], unique=False
    )

    # Create budget_signatures table
    op.create_table(
        "budget_signatures",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("budget_id", sa.UUID(), nullable=False),
        # Signature type
        sa.Column("signature_type", sa.String(length=30), nullable=False),
        # Signed items (for partial acceptance)
        sa.Column("signed_items", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # Signer information
        sa.Column("signed_by_name", sa.String(length=200), nullable=False),
        sa.Column("signed_by_email", sa.String(length=255), nullable=True),
        sa.Column("relationship_to_patient", sa.String(length=30), nullable=False),
        # Signature method
        sa.Column("signature_method", sa.String(length=30), nullable=False),
        sa.Column("signature_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # Audit information
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=False),
        # External provider integration
        sa.Column("external_signature_id", sa.String(length=255), nullable=True),
        sa.Column("external_provider", sa.String(length=50), nullable=True),
        # Document integrity
        sa.Column("document_hash", sa.String(length=64), nullable=True),
        # Timestamp
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        # Constraints
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["budget_id"], ["budgets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_budget_signatures_budget", "budget_signatures", ["budget_id"], unique=False
    )
    op.create_index(
        "idx_budget_signatures_clinic", "budget_signatures", ["clinic_id"], unique=False
    )

    # Create budget_history table
    op.create_table(
        "budget_history",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("budget_id", sa.UUID(), nullable=False),
        # Action
        sa.Column("action", sa.String(length=30), nullable=False),
        # Actor
        sa.Column("changed_by", sa.UUID(), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        # State snapshots
        sa.Column("previous_state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("new_state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # Notes
        sa.Column("notes", sa.Text(), nullable=True),
        # Constraints
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["budget_id"], ["budgets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["changed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_budget_history_budget", "budget_history", ["budget_id"], unique=False)
    op.create_index("idx_budget_history_clinic", "budget_history", ["clinic_id"], unique=False)
    op.create_index("idx_budget_history_changed_at", "budget_history", ["changed_at"], unique=False)


def downgrade() -> None:
    # Drop budget_history
    op.drop_index("idx_budget_history_changed_at", table_name="budget_history")
    op.drop_index("idx_budget_history_clinic", table_name="budget_history")
    op.drop_index("idx_budget_history_budget", table_name="budget_history")
    op.drop_table("budget_history")

    # Drop budget_signatures
    op.drop_index("idx_budget_signatures_clinic", table_name="budget_signatures")
    op.drop_index("idx_budget_signatures_budget", table_name="budget_signatures")
    op.drop_table("budget_signatures")

    # Drop budget_items
    op.drop_index("idx_budget_items_tooth_treatment", table_name="budget_items")
    op.drop_index("idx_budget_items_tooth", table_name="budget_items")
    op.drop_index("idx_budget_items_status", table_name="budget_items")
    op.drop_index("idx_budget_items_catalog", table_name="budget_items")
    op.drop_index("idx_budget_items_budget", table_name="budget_items")
    op.drop_table("budget_items")

    # Drop budgets
    op.drop_index("idx_budgets_parent", table_name="budgets")
    op.drop_index("idx_budgets_valid_until", table_name="budgets")
    op.drop_index("idx_budgets_clinic_status", table_name="budgets")
    op.drop_index("idx_budgets_clinic_patient", table_name="budgets")
    op.drop_index("idx_budgets_clinic", table_name="budgets")
    op.drop_table("budgets")
