"""Promote cabinets from JSONB to a real table.

Fase B.2 chunk 3:

* New table ``cabinets`` with (id, clinic_id, name, color, display_order,
  is_active, created_at, updated_at). Unique constraint on
  (clinic_id, name).
* Seeded from every clinic's ``clinic.cabinets`` JSONB, preserving
  insertion order.
* ``appointments.cabinet_id`` added as a FK to ``cabinets.id`` and
  backfilled from the existing ``appointments.cabinet`` string by
  (clinic_id, name) match.
* Unique slot index rebuilt on ``cabinet_id`` (instead of ``cabinet``
  string).
* ``clinic.cabinets`` JSONB column is dropped. ``appointments.cabinet``
  stays as a denormalized name for legacy callers and is kept in sync
  on cabinet rename.

Revision ID: v2w3x4y5z6a7
Revises: u1v2w3x4y5z6
Create Date: 2026-04-20

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "v2w3x4y5z6a7"
down_revision: str | None = "u1v2w3x4y5z6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- cabinets table ---
    op.create_table(
        "cabinets",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "clinic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinics.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("color", sa.String(length=7), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
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
    )
    op.create_index("ix_cabinets_clinic_id", "cabinets", ["clinic_id"])
    op.create_unique_constraint("uq_cabinet_clinic_name", "cabinets", ["clinic_id", "name"])

    # --- backfill cabinets from clinic.cabinets JSONB ---
    op.execute(
        """
        INSERT INTO cabinets (id, clinic_id, name, color, display_order, is_active, created_at, updated_at)
        SELECT
            gen_random_uuid(),
            c.id,
            cab.value->>'name',
            cab.value->>'color',
            (cab.ordinality - 1)::int,
            true,
            now(),
            now()
        FROM clinics c
        CROSS JOIN LATERAL jsonb_array_elements(c.cabinets) WITH ORDINALITY AS cab
        WHERE c.cabinets IS NOT NULL
          AND jsonb_typeof(c.cabinets) = 'array'
          AND (cab.value->>'name') IS NOT NULL
        """
    )

    # --- appointments.cabinet_id ---
    op.add_column(
        "appointments",
        sa.Column("cabinet_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Backfill cabinet_id by matching on (clinic_id, cabinet name).
    op.execute(
        """
        UPDATE appointments a
        SET cabinet_id = cab.id
        FROM cabinets cab
        WHERE a.clinic_id = cab.clinic_id
          AND a.cabinet = cab.name
        """
    )

    # Any appointment whose cabinet string didn't resolve (should not
    # happen in a clean DB) gets adopted by the first cabinet of its
    # clinic — as a last resort to keep the NOT NULL constraint valid.
    op.execute(
        """
        UPDATE appointments a
        SET cabinet_id = (
            SELECT c.id FROM cabinets c
            WHERE c.clinic_id = a.clinic_id
            ORDER BY c.display_order ASC
            LIMIT 1
        )
        WHERE a.cabinet_id IS NULL
        """
    )

    op.alter_column("appointments", "cabinet_id", nullable=False)
    op.create_foreign_key(
        "fk_appointments_cabinet_id",
        "appointments",
        "cabinets",
        ["cabinet_id"],
        ["id"],
    )
    op.create_index("ix_appointments_cabinet_id", "appointments", ["cabinet_id"])

    # --- swap the unique slot index ---
    op.drop_index("idx_appointment_slot", table_name="appointments")
    op.create_index(
        "idx_appointment_slot",
        "appointments",
        ["clinic_id", "cabinet_id", "professional_id", "start_time"],
        unique=True,
        postgresql_where=sa.text("status <> 'cancelled'"),
    )

    # --- clinic.cabinets JSONB is no longer the source of truth ---
    op.drop_column("clinics", "cabinets")


def downgrade() -> None:
    op.add_column(
        "clinics",
        sa.Column(
            "cabinets",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )

    # Rebuild clinic.cabinets JSONB from the cabinets table.
    op.execute(
        """
        UPDATE clinics c
        SET cabinets = coalesce(cab_array, '[]'::jsonb)
        FROM (
            SELECT clinic_id,
                   jsonb_agg(
                       jsonb_build_object('name', name, 'color', color)
                       ORDER BY display_order
                   ) AS cab_array
            FROM cabinets
            GROUP BY clinic_id
        ) AS src
        WHERE c.id = src.clinic_id
        """
    )

    op.drop_index("idx_appointment_slot", table_name="appointments")
    op.create_index(
        "idx_appointment_slot",
        "appointments",
        ["clinic_id", "cabinet", "professional_id", "start_time"],
        unique=True,
        postgresql_where=sa.text("status <> 'cancelled'"),
    )

    op.drop_index("ix_appointments_cabinet_id", table_name="appointments")
    op.drop_constraint("fk_appointments_cabinet_id", "appointments", type_="foreignkey")
    op.drop_column("appointments", "cabinet_id")

    op.drop_constraint("uq_cabinet_clinic_name", "cabinets", type_="unique")
    op.drop_index("ix_cabinets_clinic_id", table_name="cabinets")
    op.drop_table("cabinets")
