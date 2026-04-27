"""billing — Invoice.pdf_stale flag.

Set by compliance modules (Verifactu) after regenerating the fiscal
record so the previously rendered PDF/QR is known to be obsolete. UI
shows a badge and offers re-download.

Revision ID: bil_0002
Revises: bil_0001
Create Date: 2026-04-27
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "bil_0002"
down_revision: str | None = "bil_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "invoices",
        sa.Column(
            "pdf_stale",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.alter_column("invoices", "pdf_stale", server_default=None)


def downgrade() -> None:
    op.drop_column("invoices", "pdf_stale")
