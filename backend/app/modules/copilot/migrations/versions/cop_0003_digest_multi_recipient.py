"""copilot module — digest v2: multi-recipient list + tz-aware hour.

Replaces the single ``digest_recipient_user_id`` FK column with a JSONB
``digest_recipient_user_ids`` array (one email per recipient, each scoped
to that recipient's role). ``digest_hour`` is now interpreted in the
clinic's timezone by the task — no schema change for that.

Revision ID: cop_0003
Revises: cop_0002
Create Date: 2026-06-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "cop_0003"
down_revision: str | None = "cop_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "copilot_settings",
        sa.Column(
            "digest_recipient_user_ids",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
        ),
    )
    # Backfill the array from the single recipient, where one was set.
    op.execute(
        """
        UPDATE copilot_settings
        SET digest_recipient_user_ids =
            jsonb_build_array(digest_recipient_user_id::text)
        WHERE digest_recipient_user_id IS NOT NULL
        """
    )
    op.drop_column("copilot_settings", "digest_recipient_user_id")


def downgrade() -> None:
    op.add_column(
        "copilot_settings",
        sa.Column(
            "digest_recipient_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    # Restore the first recipient (best effort — extra recipients are lost).
    op.execute(
        """
        UPDATE copilot_settings
        SET digest_recipient_user_id =
            (digest_recipient_user_ids->>0)::uuid
        WHERE jsonb_array_length(digest_recipient_user_ids) > 0
        """
    )
    op.drop_column("copilot_settings", "digest_recipient_user_ids")
