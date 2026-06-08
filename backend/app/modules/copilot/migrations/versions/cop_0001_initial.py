"""copilot module — conversations, messages, settings.

Revision ID: cop_0001
Revises: 0001
Create Date: 2026-06-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "cop_0001"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = ("copilot",)
# copilot_conversations.session_id FKs agent_sessions, created by the core
# `0003_agents_core` migration. Without this edge alembic may run cop_0001
# (branched off 0001) before 0003 on a clean upgrade, so the FK target
# doesn't exist yet. depends_on forces the correct order.
depends_on: str | Sequence[str] | None = "0003"


def upgrade() -> None:
    op.create_table(
        "copilot_settings",
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=20), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("redaction_enabled", sa.Boolean(), nullable=False),
        sa.Column("monthly_token_limit", sa.Integer(), nullable=True),
        sa.Column("monthly_cost_limit_cents", sa.Integer(), nullable=True),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("period_output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("period_cost_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("clinic_id"),
    )

    op.create_table(
        "copilot_conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=True),
        sa.Column("context", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("provider", sa.String(length=20), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("total_input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["agent_sessions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_copilot_conversations_clinic_id"), "copilot_conversations", ["clinic_id"]
    )
    op.create_index(op.f("ix_copilot_conversations_user_id"), "copilot_conversations", ["user_id"])

    op.create_table(
        "copilot_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("seq", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["copilot_conversations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_copilot_messages_conversation_id"), "copilot_messages", ["conversation_id"]
    )
    op.create_index(op.f("ix_copilot_messages_clinic_id"), "copilot_messages", ["clinic_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_copilot_messages_clinic_id"), table_name="copilot_messages")
    op.drop_index(op.f("ix_copilot_messages_conversation_id"), table_name="copilot_messages")
    op.drop_table("copilot_messages")
    op.drop_index(op.f("ix_copilot_conversations_user_id"), table_name="copilot_conversations")
    op.drop_index(op.f("ix_copilot_conversations_clinic_id"), table_name="copilot_conversations")
    op.drop_table("copilot_conversations")
    op.drop_table("copilot_settings")
