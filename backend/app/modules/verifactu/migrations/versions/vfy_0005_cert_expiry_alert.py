"""verifactu — track last cert-expiry alert per certificate.

Adds ``verifactu_certificates.last_expiry_alert_at`` so the daily
expiry-check job (``services.cert_expiry``) can throttle alerts to
one per certificate per 24 h.

Revision ID: vfy_0005
Revises: vfy_0004
Create Date: 2026-04-27
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "vfy_0005"
down_revision: str | None = "vfy_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "verifactu_certificates",
        sa.Column(
            "last_expiry_alert_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("verifactu_certificates", "last_expiry_alert_at")
