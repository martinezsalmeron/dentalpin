"""Add core module lifecycle tables.

Creates three core tables for the module system:

* ``core_module`` — one row per discovered module, tracking lifecycle
  state (uninstalled, to_install, installed, to_upgrade, to_remove,
  disabled), version, applied Alembic revision, and a JSONB snapshot
  of the manifest at install time.
* ``core_module_operation_log`` — append-only log of install/uninstall/
  upgrade steps for crash recovery.
* ``core_external_id`` — pointers from stable ``xml_id`` to records
  owned by a module so they can be updated on upgrade and removed on
  uninstall.

Revision ID: u1v2w3x4y5z6
Revises: t0u1v2w3x4y5
Create Date: 2026-04-20

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "u1v2w3x4y5z6"
down_revision: str | None = "t0u1v2w3x4y5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "core_module",
        sa.Column("name", sa.String(length=100), primary_key=True),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("state", sa.String(length=30), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("removable", sa.Boolean(), nullable=False),
        sa.Column("auto_install", sa.Boolean(), nullable=False),
        sa.Column("installed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "last_state_change",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("base_revision", sa.String(length=64), nullable=True),
        sa.Column("applied_revision", sa.String(length=64), nullable=True),
        sa.Column(
            "manifest_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "state IN ('uninstalled','to_install','installed','to_upgrade','to_remove','disabled')",
            name="ck_core_module_state",
        ),
        sa.CheckConstraint(
            "category IN ('official','community')",
            name="ck_core_module_category",
        ),
    )

    op.create_table(
        "core_module_operation_log",
        sa.Column(
            "id",
            sa.BigInteger(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "module_name",
            sa.String(length=100),
            sa.ForeignKey("core_module.name", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("operation", sa.String(length=30), nullable=False),
        sa.Column("step", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "details",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "operation IN ('install','uninstall','upgrade')",
            name="ck_core_module_op_operation",
        ),
        sa.CheckConstraint(
            "status IN ('started','completed','failed')",
            name="ck_core_module_op_status",
        ),
    )
    op.create_index(
        "ix_core_module_operation_log_module",
        "core_module_operation_log",
        ["module_name"],
    )
    op.create_index(
        "ix_core_module_operation_log_created",
        "core_module_operation_log",
        ["created_at"],
    )

    op.create_table(
        "core_external_id",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("module_name", sa.String(length=100), nullable=False),
        sa.Column("xml_id", sa.String(length=255), nullable=False),
        sa.Column("table_name", sa.String(length=100), nullable=False),
        sa.Column("record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "noupdate",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("module_name", "xml_id", name="uq_core_external_id_module_xml"),
    )
    op.create_index("ix_core_external_id_module", "core_external_id", ["module_name"])
    op.create_index(
        "ix_core_external_id_table_record",
        "core_external_id",
        ["table_name", "record_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_core_external_id_table_record", table_name="core_external_id")
    op.drop_index("ix_core_external_id_module", table_name="core_external_id")
    op.drop_table("core_external_id")

    op.drop_index(
        "ix_core_module_operation_log_created",
        table_name="core_module_operation_log",
    )
    op.drop_index(
        "ix_core_module_operation_log_module",
        table_name="core_module_operation_log",
    )
    op.drop_table("core_module_operation_log")

    op.drop_table("core_module")
