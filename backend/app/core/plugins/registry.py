"""Module registry for tracking loaded modules."""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import BaseModule

logger = logging.getLogger(__name__)


class ModuleRegistry:
    """Registry that tracks all loaded modules.

    Provides methods to query loaded modules and their capabilities.
    """

    def __init__(self) -> None:
        self._modules: dict[str, BaseModule] = {}

    def register(self, module: "BaseModule") -> None:
        """Register a module instance."""
        if module.name in self._modules:
            raise ValueError(f"Module '{module.name}' is already registered")
        self._modules[module.name] = module
        logger.info(f"Registered module: {module.name} v{module.version}")

    def get(self, name: str) -> "BaseModule | None":
        """Get a module by name, or None if not found."""
        return self._modules.get(name)

    def is_loaded(self, name: str) -> bool:
        """Check if a module is loaded."""
        return name in self._modules

    def list_modules(self) -> list["BaseModule"]:
        """Return list of all loaded modules."""
        return list(self._modules.values())

    def get_all_permissions(self) -> list[str]:
        """Return all permissions from all loaded modules."""
        permissions: list[str] = []
        for module in self._modules.values():
            permissions.extend(module.get_permissions())
        return permissions


# Global singleton instance
module_registry = ModuleRegistry()
