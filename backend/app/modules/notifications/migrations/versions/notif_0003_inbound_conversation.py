"""notifications: inbound direction + conversation thread.

Adds ``direction`` (outbound/inbound) and ``body_text`` (literal text for
inbound messages and free-form session sends) to ``communication_messages``,
plus a thread-read index. Enables the bidirectional WhatsApp conversation
(Phase 2A). Data preserved; existing rows backfilled to ``outbound``.

Revision ID: notif_0003
Revises: notif_0002
Create Date: 2026-06-26

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "notif_0003"
down_revision: str | None = "notif_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "communication_messages",
        sa.Column("direction", sa.String(length=20), nullable=False, server_default="outbound"),
    )
    op.add_column(
        "communication_messages",
        sa.Column("body_text", sa.Text(), nullable=True),
    )
    op.alter_column("communication_messages", "direction", server_default=None)
    op.create_index(
        "idx_communication_messages_thread",
        "communication_messages",
        ["clinic_id", "patient_id", "channel", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_communication_messages_thread", table_name="communication_messages")
    op.drop_column("communication_messages", "body_text")
    op.drop_column("communication_messages", "direction")
