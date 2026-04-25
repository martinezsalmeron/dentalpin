"""verifactu — drop emisor identity columns from settings.

The clinic's NIF and legal name (Razón social) live on ``clinics``
(``tax_id`` + ``legal_name``) so every module reads from a single
source. The verifactu hook reads them from the clinic at use time
instead of duplicating into ``verifactu_settings``.

Revision ID: vfy_0003
Revises: vfy_0002
Create Date: 2026-04-25
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "vfy_0003"
down_revision: str | None = "vfy_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("verifactu_settings", "nombre_razon_emisor")
    op.drop_column("verifactu_settings", "nif_emisor")


def downgrade() -> None:
    op.add_column(
        "verifactu_settings",
        sa.Column("nif_emisor", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "verifactu_settings",
        sa.Column("nombre_razon_emisor", sa.String(length=200), nullable=True),
    )
