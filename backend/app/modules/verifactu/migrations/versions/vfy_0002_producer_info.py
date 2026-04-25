"""verifactu — add SIF producer fields + declaración responsable signature.

Adds the producer (productor del SIF) identification to per-clinic
``verifactu_settings`` so each deployment can declare who is legally
responsible as productor: the SaaS operator, an integrator, or the
clinic itself when it self-hosts (autodesarrollo).

Existing rows are left blank — the wizard prompts the operator on first
activation. Env vars ``VERIFACTU_VENDOR_NIF`` / ``VERIFACTU_VENDOR_NAME``
are used as the default values shown in the wizard, but the canonical
source of truth is the DB row once filled.

Revision ID: vfy_0002
Revises: vfy_0001
Create Date: 2026-04-25
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "vfy_0002"
down_revision: str | None = "vfy_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "verifactu_settings",
        sa.Column("producer_nif", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "verifactu_settings",
        sa.Column("producer_name", sa.String(length=200), nullable=True),
    )
    op.add_column(
        "verifactu_settings",
        sa.Column(
            "producer_id_sistema",
            sa.String(length=2),
            nullable=False,
            server_default="DP",
        ),
    )
    op.add_column(
        "verifactu_settings",
        sa.Column("producer_version", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "verifactu_settings",
        sa.Column(
            "declaracion_responsable_signed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "verifactu_settings",
        sa.Column("declaracion_responsable_signed_by", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_verifactu_settings_declaracion_signer",
        "verifactu_settings",
        "users",
        ["declaracion_responsable_signed_by"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_verifactu_settings_declaracion_signer",
        "verifactu_settings",
        type_="foreignkey",
    )
    op.drop_column("verifactu_settings", "declaracion_responsable_signed_by")
    op.drop_column("verifactu_settings", "declaracion_responsable_signed_at")
    op.drop_column("verifactu_settings", "producer_version")
    op.drop_column("verifactu_settings", "producer_id_sistema")
    op.drop_column("verifactu_settings", "producer_name")
    op.drop_column("verifactu_settings", "producer_nif")
