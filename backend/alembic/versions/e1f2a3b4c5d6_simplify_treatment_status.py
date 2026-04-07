"""Simplify treatment status from 3 to 2 categories.

Revision ID: e1f2a3b4c5d6
Revises: d0e1f2a3b4c5
Create Date: 2024-04-07

Changes:
- Converts 'preexisting' and 'performed' to 'existing'
- New statuses: 'existing', 'planned'
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "e1f2a3b4c5d6"
down_revision = "d0e1f2a3b4c5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Convert preexisting and performed to existing
    op.execute(
        "UPDATE tooth_treatments SET status = 'existing' "
        "WHERE status IN ('preexisting', 'performed')"
    )


def downgrade() -> None:
    # Note: We cannot perfectly reverse this migration since we lose
    # the distinction between preexisting and performed.
    # All 'existing' records will be converted back to 'performed'.
    op.execute("UPDATE tooth_treatments SET status = 'performed' WHERE status = 'existing'")
