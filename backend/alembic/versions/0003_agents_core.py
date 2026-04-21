"""core — AI agent integration tables.

Introduces four tables backing :mod:`app.core.agents`:

* ``agents`` — per-clinic agent definitions (name, type, mode, config).
* ``agent_sessions`` — one row per agent run / conversation, groups
  tool calls and approvals under a single correlation id.
* ``agent_approval_queue`` — pending actions awaiting human review in
  supervised mode.
* ``agent_audit_logs`` — immutable record of every tool invocation
  attempted by any agent in the system.

These tables live in core because the agent contract is infra that all
modules depend on, not a feature of any one module.

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("type", sa.String(length=100), nullable=False),
        sa.Column("mode", sa.String(length=20), nullable=False),
        sa.Column(
            "config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="active",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agents_clinic_id", "agents", ["clinic_id"])
    op.create_index("ix_agents_clinic_type", "agents", ["clinic_id", "type"])

    op.create_table(
        "agent_sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("agent_id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("supervisor_id", sa.UUID(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="active",
        ),
        sa.Column(
            "session_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["supervisor_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_sessions_agent_id", "agent_sessions", ["agent_id"])
    op.create_index("ix_agent_sessions_clinic_id", "agent_sessions", ["clinic_id"])

    op.create_table(
        "agent_approval_queue",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("agent_id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("tool_name", sa.String(length=200), nullable=False),
        sa.Column(
            "arguments",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("reason", sa.String(length=500), nullable=True),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("reviewed_by", sa.UUID(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_notes", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["agent_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_approval_queue_agent_id", "agent_approval_queue", ["agent_id"])
    op.create_index("ix_agent_approval_queue_session_id", "agent_approval_queue", ["session_id"])
    op.create_index("ix_agent_approval_queue_clinic_id", "agent_approval_queue", ["clinic_id"])
    op.create_index(
        "ix_approval_pending",
        "agent_approval_queue",
        ["clinic_id", "status", "created_at"],
    )

    op.create_table(
        "agent_audit_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("agent_id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("supervisor_id", sa.UUID(), nullable=True),
        sa.Column("tool_name", sa.String(length=200), nullable=False),
        sa.Column(
            "tool_arguments",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error", sa.String(length=2000), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "execution_time_ms",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["agent_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["supervisor_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_audit_logs_agent_id", "agent_audit_logs", ["agent_id"])
    op.create_index("ix_agent_audit_logs_session_id", "agent_audit_logs", ["session_id"])
    op.create_index("ix_agent_audit_logs_clinic_id", "agent_audit_logs", ["clinic_id"])
    op.create_index("ix_agent_audit_logs_tool_name", "agent_audit_logs", ["tool_name"])
    op.create_index("ix_audit_clinic_time", "agent_audit_logs", ["clinic_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_clinic_time", table_name="agent_audit_logs")
    op.drop_index("ix_agent_audit_logs_tool_name", table_name="agent_audit_logs")
    op.drop_index("ix_agent_audit_logs_clinic_id", table_name="agent_audit_logs")
    op.drop_index("ix_agent_audit_logs_session_id", table_name="agent_audit_logs")
    op.drop_index("ix_agent_audit_logs_agent_id", table_name="agent_audit_logs")
    op.drop_table("agent_audit_logs")

    op.drop_index("ix_approval_pending", table_name="agent_approval_queue")
    op.drop_index("ix_agent_approval_queue_clinic_id", table_name="agent_approval_queue")
    op.drop_index("ix_agent_approval_queue_session_id", table_name="agent_approval_queue")
    op.drop_index("ix_agent_approval_queue_agent_id", table_name="agent_approval_queue")
    op.drop_table("agent_approval_queue")

    op.drop_index("ix_agent_sessions_clinic_id", table_name="agent_sessions")
    op.drop_index("ix_agent_sessions_agent_id", table_name="agent_sessions")
    op.drop_table("agent_sessions")

    op.drop_index("ix_agents_clinic_type", table_name="agents")
    op.drop_index("ix_agents_clinic_id", table_name="agents")
    op.drop_table("agents")
