"""verifactu — record attempts + rejected alert throttle.

Two related changes for the Subsanación flow:

* ``verifactu_record_attempts`` — preserves every XML payload + huella
  generated for a record before it is regenerated. RD 1007/2023 art. 8
  requires conservar la trazabilidad de todos los registros generados.
* ``verifactu_settings.last_rejected_alert_at`` — throttle column so
  admins get at most one rejection alert per clinic per 30 min.

Revision ID: vfy_0006
Revises: vfy_0005
Create Date: 2026-04-27
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "vfy_0006"
down_revision: str | None = "vfy_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "verifactu_settings",
        sa.Column(
            "last_rejected_alert_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.create_table(
        "verifactu_record_attempts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("record_id", sa.UUID(), nullable=False),
        sa.Column("attempt_no", sa.Integer(), nullable=False),
        sa.Column("xml_payload", sa.Text(), nullable=False),
        sa.Column("huella", sa.String(length=64), nullable=False),
        sa.Column("state", sa.String(length=30), nullable=False),
        sa.Column("aeat_codigo_error", sa.Integer(), nullable=True),
        sa.Column("aeat_descripcion_error", sa.Text(), nullable=True),
        sa.Column("aeat_response_xml", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["record_id"], ["verifactu_records.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("record_id", "attempt_no", name="uq_verifactu_attempt_record_no"),
    )
    op.create_index(
        "ix_verifactu_record_attempts_record_id",
        "verifactu_record_attempts",
        ["record_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_verifactu_record_attempts_record_id",
        table_name="verifactu_record_attempts",
    )
    op.drop_table("verifactu_record_attempts")
    op.drop_column("verifactu_settings", "last_rejected_alert_at")
