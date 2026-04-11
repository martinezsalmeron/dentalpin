"""Add billing module tables.

Revision ID: g7h8i9j0k1l2
Revises: f6g7h8i9j0k1
Create Date: 2024-04-11

Tables created:
- invoice_series: Invoice numbering series
- invoices: Main invoice entity
- invoice_items: Invoice line items
- payments: Payment records
- invoice_history: Audit log

Also adds:
- invoiced_quantity column to budget_items
- Default invoice series for existing clinics
"""

from collections.abc import Sequence
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "g7h8i9j0k1l2"
down_revision: str | None = "f6g7h8i9j0k1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add invoiced_quantity to budget_items
    op.add_column(
        "budget_items",
        sa.Column("invoiced_quantity", sa.Integer(), nullable=False, server_default="0"),
    )

    # Create invoice_series table
    op.create_table(
        "invoice_series",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        # Series configuration
        sa.Column("prefix", sa.String(length=20), nullable=False),
        sa.Column("series_type", sa.String(length=20), nullable=False),
        sa.Column("description", sa.String(length=200), nullable=True),
        # Numbering control
        sa.Column("current_number", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reset_yearly", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_reset_year", sa.Integer(), nullable=True),
        # Flags
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        # Constraints
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clinic_id", "prefix", name="uq_invoice_series_clinic_prefix"),
    )
    op.create_index("idx_invoice_series_clinic", "invoice_series", ["clinic_id"], unique=False)
    op.create_index(
        "idx_invoice_series_clinic_type",
        "invoice_series",
        ["clinic_id", "series_type"],
        unique=False,
    )

    # Create invoices table
    op.create_table(
        "invoices",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        # Identification
        sa.Column("invoice_number", sa.String(length=50), nullable=False),
        sa.Column("series_id", sa.UUID(), nullable=False),
        sa.Column("sequential_number", sa.Integer(), nullable=False),
        # Links
        sa.Column("budget_id", sa.UUID(), nullable=True),
        sa.Column("credit_note_for_id", sa.UUID(), nullable=True),
        # Status
        sa.Column("status", sa.String(length=20), nullable=False, server_default="'draft'"),
        # Dates
        sa.Column("issue_date", sa.Date(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("payment_term_days", sa.Integer(), nullable=False, server_default="30"),
        # Billing data
        sa.Column("billing_name", sa.String(length=200), nullable=False),
        sa.Column("billing_tax_id", sa.String(length=50), nullable=True),
        sa.Column("billing_address", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("billing_email", sa.String(length=255), nullable=True),
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
        sa.Column(
            "total_paid", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0.00"
        ),
        sa.Column(
            "balance_due", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0.00"
        ),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="'EUR'"),
        # Notes
        sa.Column("internal_notes", sa.Text(), nullable=True),
        sa.Column("public_notes", sa.Text(), nullable=True),
        # Extensibility for country compliance
        sa.Column("compliance_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("document_hash", sa.String(length=64), nullable=True),
        sa.Column("previous_hash", sa.String(length=64), nullable=True),
        # Audit
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column("issued_by", sa.UUID(), nullable=True),
        # Soft delete
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        # Constraints
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
        sa.ForeignKeyConstraint(["series_id"], ["invoice_series.id"]),
        sa.ForeignKeyConstraint(["budget_id"], ["budgets.id"]),
        sa.ForeignKeyConstraint(["credit_note_for_id"], ["invoices.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["issued_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clinic_id", "invoice_number", name="uq_invoice_clinic_number"),
    )
    op.create_index("idx_invoices_clinic", "invoices", ["clinic_id"], unique=False)
    op.create_index(
        "idx_invoices_clinic_patient", "invoices", ["clinic_id", "patient_id"], unique=False
    )
    op.create_index("idx_invoices_clinic_status", "invoices", ["clinic_id", "status"], unique=False)
    op.create_index(
        "idx_invoices_clinic_issue_date", "invoices", ["clinic_id", "issue_date"], unique=False
    )
    op.create_index(
        "idx_invoices_clinic_due_date", "invoices", ["clinic_id", "due_date"], unique=False
    )
    op.create_index("idx_invoices_budget", "invoices", ["budget_id"], unique=False)
    op.create_index(
        "idx_invoices_credit_note_for", "invoices", ["credit_note_for_id"], unique=False
    )
    op.create_index("idx_invoices_series", "invoices", ["series_id"], unique=False)

    # Create invoice_items table
    op.create_table(
        "invoice_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("invoice_id", sa.UUID(), nullable=False),
        # Links
        sa.Column("budget_item_id", sa.UUID(), nullable=True),
        sa.Column("catalog_item_id", sa.UUID(), nullable=True),
        # Description
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("internal_code", sa.String(length=50), nullable=True),
        # Pricing
        sa.Column("unit_price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        # Discounts
        sa.Column("discount_type", sa.String(length=20), nullable=True),
        sa.Column("discount_value", sa.Numeric(precision=10, scale=2), nullable=True),
        # VAT
        sa.Column("vat_type_id", sa.UUID(), nullable=True),
        sa.Column("vat_rate", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("vat_exempt_reason", sa.String(length=200), nullable=True),
        # Calculated totals
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
        # Dental context
        sa.Column("tooth_number", sa.Integer(), nullable=True),
        sa.Column("surfaces", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # Display
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        # Constraints
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["budget_item_id"], ["budget_items.id"]),
        sa.ForeignKeyConstraint(["catalog_item_id"], ["treatment_catalog_items.id"]),
        sa.ForeignKeyConstraint(["vat_type_id"], ["vat_types.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_invoice_items_invoice", "invoice_items", ["invoice_id"], unique=False)
    op.create_index(
        "idx_invoice_items_budget_item", "invoice_items", ["budget_item_id"], unique=False
    )
    op.create_index(
        "idx_invoice_items_catalog_item", "invoice_items", ["catalog_item_id"], unique=False
    )

    # Create payments table
    op.create_table(
        "payments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("invoice_id", sa.UUID(), nullable=False),
        # Payment details
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("payment_method", sa.String(length=30), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("reference", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        # Audit
        sa.Column("recorded_by", sa.UUID(), nullable=False),
        # Voiding
        sa.Column("is_voided", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("voided_by", sa.UUID(), nullable=True),
        sa.Column("void_reason", sa.Text(), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        # Constraints
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recorded_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["voided_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_payments_invoice", "payments", ["invoice_id"], unique=False)
    op.create_index("idx_payments_clinic", "payments", ["clinic_id"], unique=False)
    op.create_index(
        "idx_payments_clinic_date", "payments", ["clinic_id", "payment_date"], unique=False
    )
    op.create_index(
        "idx_payments_clinic_method", "payments", ["clinic_id", "payment_method"], unique=False
    )

    # Create invoice_history table
    op.create_table(
        "invoice_history",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("invoice_id", sa.UUID(), nullable=False),
        # Action
        sa.Column("action", sa.String(length=50), nullable=False),
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
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["changed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_invoice_history_invoice", "invoice_history", ["invoice_id"], unique=False)
    op.create_index("idx_invoice_history_clinic", "invoice_history", ["clinic_id"], unique=False)
    op.create_index(
        "idx_invoice_history_changed_at", "invoice_history", ["changed_at"], unique=False
    )

    # Create default invoice series for existing clinics
    connection = op.get_bind()

    # Get all clinics
    clinics = connection.execute(sa.text("SELECT id FROM clinics")).fetchall()

    current_year = 2024

    for (clinic_id,) in clinics:
        # Create default invoice series
        invoice_series_id = uuid4()
        connection.execute(
            sa.text("""
                INSERT INTO invoice_series (
                    id, clinic_id, prefix, series_type, description,
                    current_number, reset_yearly, last_reset_year,
                    is_default, is_active, created_at, updated_at
                ) VALUES (
                    :id, :clinic_id, 'FAC', 'invoice', 'Facturas',
                    0, true, :year,
                    true, true, now(), now()
                )
            """),
            {
                "id": str(invoice_series_id),
                "clinic_id": str(clinic_id),
                "year": current_year,
            },
        )

        # Create default credit note series
        credit_note_series_id = uuid4()
        connection.execute(
            sa.text("""
                INSERT INTO invoice_series (
                    id, clinic_id, prefix, series_type, description,
                    current_number, reset_yearly, last_reset_year,
                    is_default, is_active, created_at, updated_at
                ) VALUES (
                    :id, :clinic_id, 'RECT', 'credit_note', 'Notas de Crédito',
                    0, true, :year,
                    true, true, now(), now()
                )
            """),
            {
                "id": str(credit_note_series_id),
                "clinic_id": str(clinic_id),
                "year": current_year,
            },
        )


def downgrade() -> None:
    # Drop invoice_history
    op.drop_index("idx_invoice_history_changed_at", table_name="invoice_history")
    op.drop_index("idx_invoice_history_clinic", table_name="invoice_history")
    op.drop_index("idx_invoice_history_invoice", table_name="invoice_history")
    op.drop_table("invoice_history")

    # Drop payments
    op.drop_index("idx_payments_clinic_method", table_name="payments")
    op.drop_index("idx_payments_clinic_date", table_name="payments")
    op.drop_index("idx_payments_clinic", table_name="payments")
    op.drop_index("idx_payments_invoice", table_name="payments")
    op.drop_table("payments")

    # Drop invoice_items
    op.drop_index("idx_invoice_items_catalog_item", table_name="invoice_items")
    op.drop_index("idx_invoice_items_budget_item", table_name="invoice_items")
    op.drop_index("idx_invoice_items_invoice", table_name="invoice_items")
    op.drop_table("invoice_items")

    # Drop invoices
    op.drop_index("idx_invoices_series", table_name="invoices")
    op.drop_index("idx_invoices_credit_note_for", table_name="invoices")
    op.drop_index("idx_invoices_budget", table_name="invoices")
    op.drop_index("idx_invoices_clinic_due_date", table_name="invoices")
    op.drop_index("idx_invoices_clinic_issue_date", table_name="invoices")
    op.drop_index("idx_invoices_clinic_status", table_name="invoices")
    op.drop_index("idx_invoices_clinic_patient", table_name="invoices")
    op.drop_index("idx_invoices_clinic", table_name="invoices")
    op.drop_table("invoices")

    # Drop invoice_series
    op.drop_index("idx_invoice_series_clinic_type", table_name="invoice_series")
    op.drop_index("idx_invoice_series_clinic", table_name="invoice_series")
    op.drop_table("invoice_series")

    # Remove invoiced_quantity from budget_items
    op.drop_column("budget_items", "invoiced_quantity")
