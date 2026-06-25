"""accounting_export: initial (no-op) branch.

This module is **model-free** — it owns no tables and only reads billing
data via service APIs. It still carries its own isolated Alembic branch
so ``removable=True`` holds: ``alembic downgrade accounting_export@base``
is a clean no-op that never touches another module's revisions (the
removable-branch invariant, ADR 0002 / issue #56). Add real
``op.create_table`` calls here only if the module ever grows persistent
state (e.g. export history).

Revision ID: accexp_0001
Revises:
Create Date: 2026-06-25
"""

from collections.abc import Sequence

revision: str = "accexp_0001"
# Chain off the foundational core revision so the branch has a base on a
# clean DB. No tables are created or dropped.
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = ("accounting_export",)
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """No-op: the module owns no tables."""


def downgrade() -> None:
    """No-op: the module owns no tables."""
