"""Module discovery and loading.

Discovery happens in two stages:

1. **Entry points** — the primary mechanism. Modules (internal or
   third-party) declare an entry point in the ``dentalpin.modules``
   group. This is how published PyPI packages plug in without any
   filesystem layout assumptions.

2. **Filesystem scan** — a dev-mode fallback that walks
   ``backend/app/modules/`` and imports any package containing a
   ``BaseModule`` subclass. Controlled by
   ``settings.DENTALPIN_DEV_MODULE_SCAN``. The fallback skips modules
   that an entry point already provided, so entry points win when both
   are present.

The public entry points for the rest of the app remain
:func:`load_modules` and the :class:`ModuleLoader` wrapper.
"""

from __future__ import annotations

import importlib
import logging
import pkgutil
from importlib import metadata
from pathlib import Path

from fastapi import FastAPI

from app.config import settings

from .base import BaseModule
from .registry import module_registry

logger = logging.getLogger(__name__)

ENTRY_POINT_GROUP = "dentalpin.modules"


def _resolve_load_order(modules: list[BaseModule]) -> list[BaseModule]:
    """Resolve module load order using topological sort.

    Raises ValueError if circular dependencies are detected.
    """
    module_map = {m.name: m for m in modules}
    visited: set[str] = set()
    in_stack: set[str] = set()
    order: list[BaseModule] = []

    def visit(name: str, path: list[str]) -> None:
        if name in in_stack:
            cycle = " -> ".join(path + [name])
            raise ValueError(f"Circular dependency detected: {cycle}")

        if name in visited:
            return

        if name not in module_map:
            raise ValueError(
                f"Missing dependency: '{name}' required by '{path[-1] if path else 'root'}'"
            )

        in_stack.add(name)
        module = module_map[name]

        for dep in module.dependencies:
            visit(dep, path + [name])

        in_stack.remove(name)
        visited.add(name)
        order.append(module)

    for module in modules:
        if module.name not in visited:
            visit(module.name, [])

    return order


def _instantiate_module_class(cls: type) -> BaseModule | None:
    """Instantiate a BaseModule subclass, return None on failure."""
    if not (isinstance(cls, type) and issubclass(cls, BaseModule) and cls is not BaseModule):
        return None
    try:
        return cls()
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Failed to instantiate module class %s: %s", cls.__name__, exc)
        return None


def _discover_entry_points() -> list[BaseModule]:
    """Discover modules registered as ``dentalpin.modules`` entry points."""
    modules: list[BaseModule] = []

    try:
        eps = metadata.entry_points(group=ENTRY_POINT_GROUP)
    except TypeError:
        # Python <3.10 fallback (not expected here but cheap).
        eps = metadata.entry_points().get(ENTRY_POINT_GROUP, [])  # type: ignore[union-attr]

    for ep in eps:
        try:
            cls = ep.load()
        except Exception as exc:
            logger.error("Failed to load entry point %s: %s", ep.name, exc)
            continue

        instance = _instantiate_module_class(cls)
        if instance is None:
            logger.warning("Entry point %s did not resolve to a BaseModule subclass", ep.name)
            continue

        modules.append(instance)
        logger.info("Discovered module via entry point: %s", instance.name)

    return modules


def _discover_filesystem(seen: set[str]) -> list[BaseModule]:
    """Filesystem scan fallback for dev mode.

    Skips modules already present in ``seen`` (names discovered via
    entry points).
    """
    modules: list[BaseModule] = []
    modules_path = Path(__file__).parent.parent.parent / "modules"

    if not modules_path.exists():
        logger.warning("Modules directory not found: %s", modules_path)
        return modules

    for module_info in pkgutil.iter_modules([str(modules_path)]):
        if not module_info.ispkg:
            continue

        try:
            pkg = importlib.import_module(f"app.modules.{module_info.name}")
        except Exception as exc:
            logger.error("Failed to import module %s: %s", module_info.name, exc)
            continue

        for attr_name in dir(pkg):
            cls = getattr(pkg, attr_name)
            instance = _instantiate_module_class(cls)
            if instance is None:
                continue
            if instance.name in seen:
                # Entry point already provided this module.
                break
            modules.append(instance)
            seen.add(instance.name)
            logger.info("Discovered module via filesystem scan: %s", instance.name)
            break

    return modules


def discover_modules() -> list[BaseModule]:
    """Run both discovery stages and return all unique modules."""
    modules = _discover_entry_points()
    seen = {m.name for m in modules}

    if settings.DENTALPIN_DEV_MODULE_SCAN:
        modules.extend(_discover_filesystem(seen))
    else:
        logger.info("DENTALPIN_DEV_MODULE_SCAN disabled; skipping filesystem discovery")

    return modules


def _mount_modules(app: FastAPI, modules: list[BaseModule]) -> None:
    """Mount routers + subscribe event handlers + register tools."""
    from app.core.agents.tools.registry import tool_registry
    from app.core.events import event_bus

    for module in modules:
        module_registry.register(module)
        app.include_router(
            module.get_router(),
            prefix=f"/api/v1/{module.name}",
            tags=[module.name],
        )
        logger.info("Mounted router for module: %s", module.name)

        handlers = module.get_event_handlers()
        for event_type, handler in handlers.items():
            event_bus.subscribe(event_type, handler)
            logger.info("Subscribed %s to event: %s", module.name, event_type)

        tool_registry.register_from(module)


def load_modules(app: FastAPI) -> None:
    """Discover, resolve dependencies, and load all modules."""
    modules = discover_modules()
    if not modules:
        logger.warning("No modules discovered")
        return

    try:
        ordered = _resolve_load_order(modules)
    except ValueError as exc:
        logger.error("Failed to resolve module dependencies: %s", exc)
        raise

    _mount_modules(app, ordered)
    logger.info("Loaded %d modules: %s", len(ordered), [m.name for m in ordered])


class ModuleLoader:
    """Class wrapper for module loading functionality.

    Keeps backward compatibility with the previous API used by
    ``app.main.lifespan``.
    """

    def __init__(self) -> None:
        self._modules: list[BaseModule] = []

    def discover_modules(self) -> None:
        self._modules = discover_modules()

    def load_modules(self, app: FastAPI) -> None:
        if not self._modules:
            self.discover_modules()

        if not self._modules:
            logger.warning("No modules to load")
            return

        try:
            ordered = _resolve_load_order(self._modules)
        except ValueError as exc:
            logger.error("Failed to resolve module dependencies: %s", exc)
            raise

        _mount_modules(app, ordered)
        logger.info("Loaded %d modules: %s", len(ordered), [m.name for m in ordered])
