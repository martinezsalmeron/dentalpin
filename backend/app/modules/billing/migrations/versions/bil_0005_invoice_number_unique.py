"""billing — enforce invoice-number uniqueness (fiscal backstop).

Closes audit S3/C3 (issue #93): the ``Invoice`` model comment claimed a
partial unique index ``ix_invoices_clinic_number_unique`` already
"replaced" the old constraint, but no migration ever created it, so
duplicate fiscal invoice numbers were representable at the DB level.

Two partial unique indexes, both scoped to issued rows only (drafts have
NULL identifiers and must not collide):

* ``ix_invoices_clinic_number_unique`` — (clinic_id, invoice_number):
  the human-facing document number is unique per clinic.
* ``ix_invoices_series_sequential_unique`` — (series_id,
  sequential_number): the gap-control sequential is unique per series
  (the real AEAT/Spanish-compliance invariant).

Note: if a database already holds duplicates, this migration fails
loudly on ``CREATE UNIQUE INDEX`` — that is intended. A duplicate fiscal
number is a data problem to fix, not to paper over.

Revision ID: bil_0005
Revises: bil_0004
Create Date: 2026-07-03
"""

from collections.abc import Sequence

from alembic import op

revision: str = "bil_0005"
down_revision: str | None = "bil_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_invoices_clinic_number_unique",
        "invoices",
        ["clinic_id", "invoice_number"],
        unique=True,
        postgresql_where="invoice_number IS NOT NULL",
    )
    op.create_index(
        "ix_invoices_series_sequential_unique",
        "invoices",
        ["series_id", "sequential_number"],
        unique=True,
        postgresql_where="series_id IS NOT NULL AND sequential_number IS NOT NULL",
    )


def downgrade() -> None:
    op.drop_index("ix_invoices_series_sequential_unique", table_name="invoices")
    op.drop_index("ix_invoices_clinic_number_unique", table_name="invoices")
