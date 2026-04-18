"""Add scope and arch columns to treatments; align catalog treatment_scope values.

Introduces unified Treatment.scope enum (tooth | multi_tooth | global_mouth |
global_arch) and an arch column for global_arch treatments. Also migrates
existing catalog.treatment_scope values (surface/whole_tooth → tooth).

Revision ID: t0u1v2w3x4y5
Revises: s9t0u1v2w3x4
Create Date: 2026-04-18

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "t0u1v2w3x4y5"
down_revision: str | None = "s9t0u1v2w3x4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- treatments table ---
    op.add_column(
        "treatments",
        sa.Column("scope", sa.String(length=20), nullable=False, server_default="tooth"),
    )
    op.add_column(
        "treatments",
        sa.Column("arch", sa.String(length=10), nullable=True),
    )

    # Backfill scope from existing TreatmentTooth counts (1 → tooth, 2+ → multi_tooth).
    # No existing rows will have 0 teeth (globals are new).
    op.execute(
        """
        UPDATE treatments t
        SET scope = CASE
            WHEN (SELECT COUNT(*) FROM treatment_teeth tt WHERE tt.treatment_id = t.id) >= 2
                THEN 'multi_tooth'
            ELSE 'tooth'
        END
        """
    )

    # Drop default after backfill so future inserts set scope explicitly.
    op.alter_column("treatments", "scope", server_default=None)

    op.create_check_constraint(
        "ck_treatments_scope",
        "treatments",
        "scope IN ('tooth', 'multi_tooth', 'global_mouth', 'global_arch')",
    )
    op.create_check_constraint(
        "ck_treatments_arch_matches_scope",
        "treatments",
        "(scope = 'global_arch' AND arch IS NOT NULL) OR (scope <> 'global_arch' AND arch IS NULL)",
    )
    op.create_check_constraint(
        "ck_treatments_arch_value",
        "treatments",
        "arch IS NULL OR arch IN ('upper', 'lower')",
    )

    # --- catalog: migrate legacy treatment_scope values ---
    #   surface / whole_tooth → tooth (unified scope enum).
    op.execute(
        "UPDATE treatment_catalog_items "
        "SET treatment_scope = 'tooth' "
        "WHERE treatment_scope IN ('surface', 'whole_tooth')"
    )
    op.alter_column(
        "treatment_catalog_items",
        "treatment_scope",
        server_default="tooth",
    )


def downgrade() -> None:
    # Catalog: revert to legacy values (all map to 'whole_tooth' as a safe default).
    op.execute(
        "UPDATE treatment_catalog_items "
        "SET treatment_scope = 'whole_tooth' "
        "WHERE treatment_scope IN ('tooth', 'multi_tooth', 'global_mouth', 'global_arch')"
    )
    op.alter_column(
        "treatment_catalog_items",
        "treatment_scope",
        server_default="whole_tooth",
    )

    # Treatments: drop constraints and columns.
    op.drop_constraint("ck_treatments_arch_value", "treatments", type_="check")
    op.drop_constraint("ck_treatments_arch_matches_scope", "treatments", type_="check")
    op.drop_constraint("ck_treatments_scope", "treatments", type_="check")
    op.drop_column("treatments", "arch")
    op.drop_column("treatments", "scope")
