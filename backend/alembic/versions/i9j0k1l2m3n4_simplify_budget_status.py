"""Simplify budget status - remove item-level status tracking

This migration simplifies the budget workflow by removing:
1. Item-level status tracking (item_status, treatment timestamps)
2. Legacy acceptance states (partially_accepted)
3. The 'in_progress' budget state (handled at app level)

Budget status is now simplified to:
- draft: Initial, editable
- sent: Sent to patient, awaiting response
- accepted: Patient accepted, ready for treatment/invoicing
- completed: All work done
- rejected/expired/cancelled: Terminal states

Revision ID: i9j0k1l2m3n4
Revises: 9ac13662ae08
Create Date: 2025-01-15 10:00:00.000000
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision: str = "i9j0k1l2m3n4"
down_revision: str | None = "9ac13662ae08"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Update budgets: migrate old states to new simplified states
    # 'partially_accepted' -> 'accepted'
    op.execute("""
        UPDATE budgets
        SET status = 'accepted'
        WHERE status = 'partially_accepted'
    """)

    # 'sent' stays as 'sent' - it's now a valid state

    # 'in_progress' -> 'accepted' (in_progress is no longer a state)
    op.execute("""
        UPDATE budgets
        SET status = 'accepted'
        WHERE status = 'in_progress'
    """)

    # 'invoiced' -> 'completed' (invoiced is no longer a state)
    op.execute("""
        UPDATE budgets
        SET status = 'completed'
        WHERE status = 'invoiced'
    """)

    # 2. Delete rejected items from budgets that are now accepted
    op.execute("""
        DELETE FROM budget_items
        WHERE item_status = 'rejected'
        AND budget_id IN (
            SELECT id FROM budgets
            WHERE status IN ('accepted', 'completed')
        )
    """)

    # 3. Drop the index on item_status (must be done before dropping column)
    op.execute("""
        DROP INDEX IF EXISTS idx_budget_items_status
    """)

    # 4. Drop item-level status columns from budget_items
    # Check if columns exist before dropping
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns
                       WHERE table_name = 'budget_items' AND column_name = 'item_status') THEN
                ALTER TABLE budget_items DROP COLUMN item_status;
            END IF;

            IF EXISTS (SELECT 1 FROM information_schema.columns
                       WHERE table_name = 'budget_items' AND column_name = 'treatment_started_at') THEN
                ALTER TABLE budget_items DROP COLUMN treatment_started_at;
            END IF;

            IF EXISTS (SELECT 1 FROM information_schema.columns
                       WHERE table_name = 'budget_items' AND column_name = 'treatment_completed_at') THEN
                ALTER TABLE budget_items DROP COLUMN treatment_completed_at;
            END IF;

            IF EXISTS (SELECT 1 FROM information_schema.columns
                       WHERE table_name = 'budget_items' AND column_name = 'performed_by') THEN
                ALTER TABLE budget_items DROP COLUMN performed_by;
            END IF;

            IF EXISTS (SELECT 1 FROM information_schema.columns
                       WHERE table_name = 'budget_items' AND column_name = 'accepted_at') THEN
                ALTER TABLE budget_items DROP COLUMN accepted_at;
            END IF;

            IF EXISTS (SELECT 1 FROM information_schema.columns
                       WHERE table_name = 'budget_items' AND column_name = 'rejected_at') THEN
                ALTER TABLE budget_items DROP COLUMN rejected_at;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Re-add the columns
    op.add_column('budget_items', sa.Column(
        'item_status',
        sa.String(20),
        nullable=False,
        server_default='pending'
    ))
    op.add_column('budget_items', sa.Column(
        'treatment_started_at',
        sa.DateTime(timezone=True),
        nullable=True
    ))
    op.add_column('budget_items', sa.Column(
        'treatment_completed_at',
        sa.DateTime(timezone=True),
        nullable=True
    ))
    op.add_column('budget_items', sa.Column(
        'performed_by',
        sa.dialects.postgresql.UUID(as_uuid=True),
        nullable=True
    ))
    op.add_column('budget_items', sa.Column(
        'accepted_at',
        sa.DateTime(timezone=True),
        nullable=True
    ))
    op.add_column('budget_items', sa.Column(
        'rejected_at',
        sa.DateTime(timezone=True),
        nullable=True
    ))

    # Re-create the index
    op.create_index(
        'idx_budget_items_status',
        'budget_items',
        ['budget_id', 'item_status']
    )

    # Note: Cannot fully restore original data as it was deleted/modified
