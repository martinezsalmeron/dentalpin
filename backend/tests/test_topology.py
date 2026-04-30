"""Unit tests for ``app.core.plugins.topology``."""

from dataclasses import dataclass

import pytest

from app.core.plugins.topology import (
    CircularDependencyError,
    MissingDependencyError,
    topological_sort,
)


@dataclass
class _Item:
    name: str
    deps: list[str]


def _sort(items: list[_Item]) -> list[str]:
    return [i.name for i in topological_sort(items, key=lambda i: i.name, deps_of=lambda i: i.deps)]


def test_dag_returns_dependencies_before_dependents():
    items = [
        _Item("c", ["b"]),
        _Item("a", []),
        _Item("b", ["a"]),
    ]
    assert _sort(items) == ["a", "b", "c"]


def test_circular_dependency_raises():
    items = [_Item("a", ["b"]), _Item("b", ["a"])]
    with pytest.raises(CircularDependencyError) as exc:
        _sort(items)
    assert "a" in str(exc.value) and "b" in str(exc.value)


def test_missing_dependency_raises():
    items = [_Item("a", ["ghost"])]
    with pytest.raises(MissingDependencyError) as exc:
        _sort(items)
    assert "ghost" in str(exc.value)


def test_diamond_dependencies():
    items = [
        _Item("d", ["b", "c"]),
        _Item("b", ["a"]),
        _Item("c", ["a"]),
        _Item("a", []),
    ]
    order = _sort(items)
    assert order.index("a") < order.index("b")
    assert order.index("a") < order.index("c")
    assert order.index("b") < order.index("d")
    assert order.index("c") < order.index("d")
