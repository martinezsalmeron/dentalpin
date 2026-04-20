"""Tests for module discovery and topological ordering."""

from __future__ import annotations

import pytest
from fastapi import APIRouter

from app.core.plugins.base import BaseModule
from app.core.plugins.loader import _resolve_load_order


class _StubModule(BaseModule):
    """Minimal module fixture used by load-order tests."""

    def __init__(self, name: str, depends: list[str] | None = None) -> None:
        self._name = name
        self._depends = depends or []

    @property
    def name(self) -> str:  # type: ignore[override]
        return self._name

    @property
    def version(self) -> str:  # type: ignore[override]
        return "0.0.1"

    @property
    def dependencies(self) -> list[str]:  # type: ignore[override]
        return self._depends

    def get_models(self) -> list:
        return []

    def get_router(self) -> APIRouter:
        return APIRouter()


def test_topo_sort_linear_chain() -> None:
    a = _StubModule("a")
    b = _StubModule("b", ["a"])
    c = _StubModule("c", ["b"])

    order = _resolve_load_order([c, a, b])

    names = [m.name for m in order]
    assert names.index("a") < names.index("b") < names.index("c")


def test_topo_sort_diamond() -> None:
    a = _StubModule("a")
    b = _StubModule("b", ["a"])
    c = _StubModule("c", ["a"])
    d = _StubModule("d", ["b", "c"])

    order = _resolve_load_order([d, c, b, a])
    names = [m.name for m in order]

    assert names.index("a") < names.index("b")
    assert names.index("a") < names.index("c")
    assert names.index("b") < names.index("d")
    assert names.index("c") < names.index("d")


def test_topo_sort_transitive_missing_dep() -> None:
    # c depends on b which depends on a; b is missing from the list.
    a = _StubModule("a")
    c = _StubModule("c", ["b"])

    with pytest.raises(ValueError, match="Missing dependency"):
        _resolve_load_order([a, c])


def test_topo_sort_cycle_detected() -> None:
    a = _StubModule("a", ["b"])
    b = _StubModule("b", ["a"])

    with pytest.raises(ValueError, match="Circular dependency"):
        _resolve_load_order([a, b])


def test_topo_sort_self_cycle() -> None:
    m = _StubModule("m", ["m"])
    with pytest.raises(ValueError, match="Circular dependency"):
        _resolve_load_order([m])


def test_discovered_modules_include_every_module() -> None:
    """Entry points in pyproject.toml should surface every module."""
    from app.core.plugins.loader import discover_modules

    modules = discover_modules()
    names = {m.name for m in modules}
    expected = {
        "patients",
        "patients_clinical",
        "agenda",
        "patient_timeline",
        "catalog",
        "budget",
        "billing",
        "odontogram",
        "treatment_plan",
        "media",
        "notifications",
        "reports",
    }
    assert expected.issubset(names), f"missing: {expected - names}"
