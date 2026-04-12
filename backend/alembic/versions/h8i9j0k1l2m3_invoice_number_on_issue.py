"""Invoice number assigned on issue instead of creation.

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2026-04-12

Changes:
- Make invoice_number, sequential_number, series_id nullable
- Replace unique constraint with partial unique index
  (allows multiple NULL values for drafts, but enforces uniqueness for issued invoices)
"""

from sqlalchemy import text

from alembic import op

# revision identifiers, used by Alembic.
revision = "h8i9j0k1l2m3"
down_revision = "g7h8i9j0k1l2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make columns nullable
    op.alter_column("invoices", "invoice_number", nullable=True)
    op.alter_column("invoices", "sequential_number", nullable=True)
    op.alter_column("invoices", "series_id", nullable=True)

    # Drop existing unique constraint
    op.drop_constraint("uq_invoice_clinic_number", "invoices", type_="unique")

    # Create partial unique index (only for non-NULL invoice_number)
    # This allows multiple drafts without invoice_number while still
    # enforcing uniqueness for issued invoices
    op.execute(
        text(
            """
            CREATE UNIQUE INDEX ix_invoices_clinic_number_unique
            ON invoices (clinic_id, invoice_number)
            WHERE invoice_number IS NOT NULL
            """
        )
    )


def downgrade() -> None:
    # Drop partial unique index
    op.drop_index("ix_invoices_clinic_number_unique", table_name="invoices")

    # Recreate original unique constraint
    # Note: This will fail if there are any NULL values in invoice_number
    op.create_unique_constraint(
        "uq_invoice_clinic_number", "invoices", ["clinic_id", "invoice_number"]
    )

    # Make columns non-nullable
    # Note: This will fail if there are any NULL values
    op.alter_column("invoices", "invoice_number", nullable=False)
    op.alter_column("invoices", "sequential_number", nullable=False)
    op.alter_column("invoices", "series_id", nullable=False)
