"""Make billing_name nullable for draft invoices.

Revision ID: j0k1l2m3n4o5
Revises: i9j0k1l2m3n4
Create Date: 2024-04-12 14:00:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "j0k1l2m3n4o5"
down_revision: str | None = "i9j0k1l2m3n4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Make billing_name nullable for draft invoices
    # Drafts don't store billing data - it comes from patient dynamically
    op.alter_column(
        "invoices",
        "billing_name",
        existing_type=sa.String(200),
        nullable=True,
    )


def downgrade() -> None:
    # First update any NULL values to empty string
    op.execute("UPDATE invoices SET billing_name = '' WHERE billing_name IS NULL")

    op.alter_column(
        "invoices",
        "billing_name",
        existing_type=sa.String(200),
        nullable=False,
    )
