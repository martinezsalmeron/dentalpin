"""verifactu — per-clinic AEAT VAT classification overrides.

Adds ``verifactu_vat_classifications`` so the clinic admin can pin the
AEAT ``CalificacionOperacion`` / ``OperacionExenta`` value for each
catalog ``vat_type``. Lives inside the verifactu module so other
country compliance modules (Italy, France…) can ship their own
mapping tables without touching billing or catalog.

Revision ID: vfy_0004
Revises: vfy_0003
Create Date: 2026-04-25
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "vfy_0004"
down_revision: str | None = "vfy_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "verifactu_vat_classifications",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("vat_type_id", sa.UUID(), nullable=False),
        sa.Column("classification", sa.String(length=2), nullable=False),
        sa.Column("exemption_cause", sa.String(length=2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"], ["clinics.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["vat_type_id"], ["vat_types.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "clinic_id",
            "vat_type_id",
            name="uq_verifactu_vat_class_clinic_vat",
        ),
    )
    op.create_index(
        "ix_verifactu_vat_classifications_clinic_id",
        "verifactu_vat_classifications",
        ["clinic_id"],
    )
    op.create_index(
        "ix_verifactu_vat_classifications_vat_type_id",
        "verifactu_vat_classifications",
        ["vat_type_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_verifactu_vat_classifications_vat_type_id",
        table_name="verifactu_vat_classifications",
    )
    op.drop_index(
        "ix_verifactu_vat_classifications_clinic_id",
        table_name="verifactu_vat_classifications",
    )
    op.drop_table("verifactu_vat_classifications")
