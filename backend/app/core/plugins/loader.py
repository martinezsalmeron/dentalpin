"""Module loader for discovering and loading modules at startup."""

import importlib
import logging
import pkgutil
from pathlib import Path

from fastapi import FastAPI

from .base import BaseModule
from .registry import module_registry

logger = logging.getLogger(__name__)


def _resolve_load_order(modules: list[BaseModule]) -> list[BaseModule]:
    """Resolve module load order using topological sort.

    Raises ValueError if circular dependencies are detected.
    """
    # Build dependency graph
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


def _discover_modules() -> list[BaseModule]:
    """Discover all modules in app/modules/ directory."""
    modules: list[BaseModule] = []
    modules_path = Path(__file__).parent.parent.parent / "modules"

    if not modules_path.exists():
        logger.warning(f"Modules directory not found: {modules_path}")
        return modules

    for module_info in pkgutil.iter_modules([str(modules_path)]):
        if not module_info.ispkg:
            continue

        try:
            # Import the module package
            module_pkg = importlib.import_module(f"app.modules.{module_info.name}")

            # Look for a class that inherits from BaseModule
            for attr_name in dir(module_pkg):
                attr = getattr(module_pkg, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BaseModule)
                    and attr is not BaseModule
                ):
                    # Instantiate and add to list
                    instance = attr()
                    modules.append(instance)
                    logger.info(f"Discovered module: {instance.name}")
                    break
            else:
                logger.warning(f"No BaseModule subclass found in app.modules.{module_info.name}")

        except Exception as e:
            logger.error(f"Failed to load module {module_info.name}: {e}")

    return modules


def load_modules(app: FastAPI) -> None:
    """Discover, resolve dependencies, and load all modules.

    This function:
    1. Scans app/modules/ for packages with BaseModule subclasses
    2. Resolves dependency order (topological sort)
    3. Registers all models with SQLAlchemy metadata
    4. Mounts all routers under /api/v1/{module_name}/
    5. Subscribes event handlers to event bus
    """
    from app.core.events import event_bus

    # Discover modules
    modules = _discover_modules()

    if not modules:
        logger.warning("No modules discovered")
        return

    # Resolve load order
    try:
        ordered = _resolve_load_order(modules)
    except ValueError as e:
        logger.error(f"Failed to resolve module dependencies: {e}")
        raise

    # Load each module
    for module in ordered:
        # Register in registry
        module_registry.register(module)

        # Mount router
        router = module.get_router()
        app.include_router(router, prefix=f"/api/v1/{module.name}", tags=[module.name])
        logger.info(f"Mounted router for module: {module.name}")

        # Subscribe event handlers
        handlers = module.get_event_handlers()
        for event_type, handler in handlers.items():
            event_bus.subscribe(event_type, handler)
            logger.info(f"Subscribed {module.name} to event: {event_type}")

    logger.info(f"Loaded {len(ordered)} modules: {[m.name for m in ordered]}")


class ModuleLoader:
    """Class wrapper for module loading functionality."""

    def __init__(self) -> None:
        self._modules: list[BaseModule] = []

    def discover_modules(self) -> None:
        """Discover all modules in app/modules/ directory."""
        self._modules = _discover_modules()

    def load_modules(self, app: FastAPI) -> None:
        """Load discovered modules into the FastAPI app."""
        if not self._modules:
            self.discover_modules()

        if not self._modules:
            logger.warning("No modules to load")
            return

        from app.core.events import event_bus

        # Resolve load order
        try:
            ordered = _resolve_load_order(self._modules)
        except ValueError as e:
            logger.error(f"Failed to resolve module dependencies: {e}")
            raise

        # Load each module
        for module in ordered:
            module_registry.register(module)
            router = module.get_router()
            app.include_router(router, prefix=f"/api/v1/{module.name}", tags=[module.name])
            logger.info(f"Mounted router for module: {module.name}")

            handlers = module.get_event_handlers()
            for event_type, handler in handlers.items():
                event_bus.subscribe(event_type, handler)
                logger.info(f"Subscribed {module.name} to event: {event_type}")

        logger.info(f"Loaded {len(ordered)} modules: {[m.name for m in ordered]}")
