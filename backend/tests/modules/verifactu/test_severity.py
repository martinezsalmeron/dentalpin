"""severity_for() unit tests — pure function, no DB."""

from __future__ import annotations

import pytest

from app.modules.verifactu.services.severity import severity_for


@pytest.mark.parametrize(
    "state,code,expected",
    [
        ("accepted", None, "ok"),
        ("accepted_with_errors", None, "warning"),
        ("rejected", 4116, "error"),
        ("failed_validation", None, "error"),
        ("pending", None, "pending"),
        ("sending", None, "pending"),
        # transient with transport-only codes -> pending (auto-retried)
        ("failed_transient", -1, "pending"),
        ("failed_transient", 103, "pending"),
        ("failed_transient", -904, "pending"),
        ("failed_transient", None, "pending"),
        # transient with business-level codes -> error (human action)
        ("failed_transient", -2, "error"),
        ("failed_transient", 1100, "error"),
        ("failed_transient", 4116, "error"),
        # unknown / future state -> pending (don't paint red without cause)
        ("nonsense", None, "pending"),
        (None, None, "pending"),
    ],
)
def test_severity_mapping(state: str | None, code: int | None, expected: str) -> None:
    assert severity_for(state, code) == expected
