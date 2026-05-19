"""payments — extend earned ledger with per-session granularity.

Adds ``source_session_id`` + ``description`` to
``patient_earned_entries`` and swaps the single-column unique
``(treatment_id)`` for the composite ``(treatment_id, source_session_id)``
so multi-session treatments can produce one earned row per session.

Backfill is **best-effort** by design: clinics with the
``treatment_plan`` module installed will see the column populated from
the (already backfilled) single-session row created by ``tp_0006``; if
the join finds no match (e.g. payments-only deployment, deleted
treatment) the column stays NULL and the row keeps its legacy meaning.

Revision ID: pay_0002
Revises: pay_0001
Create Date: 2026-05-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "pay_0002"
down_revision: str | None = "pay_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "patient_earned_entries",
        sa.Column("source_session_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "patient_earned_entries",
        sa.Column("description", sa.String(length=160), nullable=True),
    )
    op.create_index(
        "ix_patient_earned_entries_source_session_id",
        "patient_earned_entries",
        ["source_session_id"],
    )

    # Tolerant backfill via raw SQL: only runs when treatment_plan tables
    # exist in this database. ``to_regclass`` returns NULL otherwise.
    op.execute(
        """
        DO $$
        BEGIN
            IF to_regclass('public.planned_treatment_item_sessions') IS NOT NULL
               AND to_regclass('public.planned_treatment_items') IS NOT NULL THEN
                UPDATE patient_earned_entries pee
                   SET source_session_id = ses.id
                  FROM planned_treatment_items pti
                  JOIN planned_treatment_item_sessions ses
                    ON ses.plan_item_id = pti.id
                 WHERE pti.treatment_id = pee.treatment_id
                   AND pee.source_session_id IS NULL;
            END IF;
        END $$;
        """
    )

    op.drop_constraint("uq_earned_treatment", "patient_earned_entries", type_="unique")
    op.create_unique_constraint(
        "uq_earned_treatment_session",
        "patient_earned_entries",
        ["treatment_id", "source_session_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_earned_treatment_session", "patient_earned_entries", type_="unique")
    op.create_unique_constraint("uq_earned_treatment", "patient_earned_entries", ["treatment_id"])
    op.drop_index(
        "ix_patient_earned_entries_source_session_id",
        table_name="patient_earned_entries",
    )
    op.drop_column("patient_earned_entries", "description")
    op.drop_column("patient_earned_entries", "source_session_id")
