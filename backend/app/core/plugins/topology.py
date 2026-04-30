"""Topological sort helper used by the module lifecycle.

Three places in the plugin system need the same DAG walk over module
dependencies (boot order, scheduling installs, ordering pending
operations). They share this helper instead of carrying three near-
identical copies.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import TypeVar

T = TypeVar("T")


class TopologyError(ValueError):
    """Base class for topology errors. Inherits ``ValueError`` so existing
    ``except ValueError`` blocks keep catching them."""


class CircularDependencyError(TopologyError):
    pass


class MissingDependencyError(TopologyError):
    pass


def topological_sort(
    items: Iterable[T],
    *,
    key: Callable[[T], str],
    deps_of: Callable[[T], Iterable[str]],
) -> list[T]:
    """Return ``items`` ordered so every item appears after its dependencies.

    ``deps_of(item)`` returns the names of items that must come first.
    Names not present among ``items`` raise :class:`MissingDependencyError`.
    Callers that want to silently ignore unknown deps should filter them
    in their own ``deps_of`` callable.
    """
    item_list = list(items)
    by_key: dict[str, T] = {key(item): item for item in item_list}
    visited: set[str] = set()
    in_stack: set[str] = set()
    order: list[T] = []

    def visit(name: str, path: list[str]) -> None:
        if name in in_stack:
            cycle = " -> ".join([*path, name])
            raise CircularDependencyError(f"Circular dependency detected: {cycle}")
        if name in visited:
            return
        if name not in by_key:
            origin = path[-1] if path else "root"
            raise MissingDependencyError(
                f"Missing dependency: '{name}' required by '{origin}'"
            )
        in_stack.add(name)
        for dep in deps_of(by_key[name]):
            visit(dep, [*path, name])
        in_stack.remove(name)
        visited.add(name)
        order.append(by_key[name])

    for item in item_list:
        name = key(item)
        if name not in visited:
            visit(name, [])

    return order
