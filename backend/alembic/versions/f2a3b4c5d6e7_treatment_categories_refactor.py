"""Treatment categories refactor with new visualization rules.

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2024-04-07

Changes:
- Maps old treatment types to new naming convention:
  - 'filling' → 'filling_composite'
  - 'root_canal' → 'root_canal_full'
  - 'bridge_pontic' → 'pontic'
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "f2a3b4c5d6e7"
down_revision = "e1f2a3b4c5d6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Map old treatment types to new naming convention
    # These mappings allow the new visualization rules to work correctly
    op.execute(
        "UPDATE tooth_treatments SET treatment_type = 'filling_composite' "
        "WHERE treatment_type = 'filling'"
    )
    op.execute(
        "UPDATE tooth_treatments SET treatment_type = 'root_canal_full' "
        "WHERE treatment_type = 'root_canal'"
    )
    op.execute(
        "UPDATE tooth_treatments SET treatment_type = 'pontic' "
        "WHERE treatment_type = 'bridge_pontic'"
    )


def downgrade() -> None:
    # Revert to old treatment type names
    op.execute(
        "UPDATE tooth_treatments SET treatment_type = 'filling' "
        "WHERE treatment_type = 'filling_composite'"
    )
    op.execute(
        "UPDATE tooth_treatments SET treatment_type = 'root_canal' "
        "WHERE treatment_type = 'root_canal_full'"
    )
    op.execute(
        "UPDATE tooth_treatments SET treatment_type = 'bridge_pontic' "
        "WHERE treatment_type = 'pontic'"
    )
