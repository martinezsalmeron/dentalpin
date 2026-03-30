"""Base module abstract class for the plugin system."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter
from sqlalchemy.orm import DeclarativeBase


class BaseModule(ABC):
    """Abstract base class that all modules must inherit from.

    Each module is a self-contained feature that provides:
    - SQLAlchemy models
    - FastAPI router
    - Event handlers (optional)
    - RBAC permissions (optional)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique module identifier, e.g. 'clinical', 'supplies'."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Semver string, e.g. '0.1.0'."""
        pass

    @property
    def dependencies(self) -> list[str]:
        """List of required module names that must be loaded first."""
        return []

    @abstractmethod
    def get_models(self) -> list[type[DeclarativeBase]]:
        """Return SQLAlchemy models to register with the database."""
        pass

    @abstractmethod
    def get_router(self) -> APIRouter:
        """Return FastAPI router to mount at /api/v1/{module_name}/."""
        pass

    def get_event_handlers(self) -> dict[str, Callable[[dict[str, Any]], None]]:
        """Return map of event_name -> handler function.

        Handlers receive event data as a dict and should not return anything.
        """
        return {}

    def get_permissions(self) -> list[str]:
        """Return custom permissions this module adds to RBAC.

        Format: 'resource.action', e.g. 'patients.read', 'appointments.manage'
        """
        return []
