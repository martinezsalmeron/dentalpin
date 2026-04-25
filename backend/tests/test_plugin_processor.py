"""Unit tests for the plugin processor's Alembic helpers.

Covers the pieces added while hardening the uninstall pipeline (issue #56):
``_parent_revision``, ``_module_branch_label``, ``_downgrade_target_for``
and ``_pg_dump_dsn``. All four are pure functions over the real Alembic
script directory — no DB connection needed.
"""

from __future__ import annotations

from app.core.plugins.processor import (
    _count_owned_revisions,
    _downgrade_target_for,
    _module_branch_label,
    _parent_revision,
    _pg_dump_dsn,
)


def test_parent_revision_returns_immediate_ancestor() -> None:
    assert _parent_revision("pat_0001") == "0001"


def test_parent_revision_of_core_initial_is_base() -> None:
    assert _parent_revision("0001") == "base"


def test_module_branch_label_for_schedules_branch_head() -> None:
    assert _module_branch_label("sch_0001") == "schedules"


def test_module_branch_label_on_main_chain_is_none() -> None:
    # Revisions on the main linear chain carry no branch label.
    assert _module_branch_label("pat_0001") is None
    assert _module_branch_label("tp_0002") is None


def test_downgrade_target_uses_branch_relative_for_branched_module() -> None:
    # schedules owns exactly one revision (sch_0001), so the relative
    # target walks the branch one step down — landing on the shared
    # ancestor without touching the main branch.
    assert _downgrade_target_for("schedules", "sch_0001") == "schedules@-1"


def test_downgrade_target_falls_back_to_parent_for_unlabelled_revision() -> None:
    # Should not happen for removable modules post-audit, but the
    # defensive path must still return the parent so behaviour is
    # predictable if a future contributor forgets ``branch_labels``.
    assert _downgrade_target_for("patients", "pat_0001") == "0001"


def test_downgrade_target_base_when_no_base_revision() -> None:
    assert _downgrade_target_for("schedules", None) == "base"


def test_count_owned_revisions_for_schedules() -> None:
    assert _count_owned_revisions("schedules") == 1


def test_count_owned_revisions_for_legacy_main_linear_module_is_zero() -> None:
    # reports has no migrations/versions/ directory at all.
    assert _count_owned_revisions("reports") == 0


def test_pg_dump_dsn_strips_async_driver_prefix() -> None:
    assert _pg_dump_dsn("postgresql+asyncpg://u:p@h/db") == "postgresql://u:p@h/db"
    assert _pg_dump_dsn("postgresql://u:p@h/db") == "postgresql://u:p@h/db"
