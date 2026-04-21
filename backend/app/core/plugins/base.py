"""Base module abstract class for the plugin system."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, ClassVar

from fastapi import APIRouter
from sqlalchemy.orm import DeclarativeBase

from .manifest import Manifest

if TYPE_CHECKING:
    from app.core.agents.base import BaseAgent
    from app.core.agents.tools.tool import Tool

    from .context import ModuleContext


class BaseModule(ABC):
    """Abstract base class that all modules must inherit from.

    Each module is a self-contained feature that provides:
    - SQLAlchemy models
    - FastAPI router
    - Event handlers (optional)
    - RBAC permissions (optional)
    - Lifecycle hooks (optional: install, uninstall, post_upgrade)

    Modules declare metadata through a class-level ``manifest`` dict. When
    ``manifest`` is not set, the legacy ``name``/``version``/``dependencies``
    properties are used to build one on the fly. New modules should always
    set ``manifest`` directly.
    """

    # Declarative manifest. New modules set this as a class attribute.
    # Legacy modules can omit it; the registry falls back to the legacy
    # properties below to construct a manifest.
    manifest: ClassVar[dict[str, Any] | None] = None

    # --- Identity (legacy + derived from manifest) -----------------------

    @property
    def name(self) -> str:
        """Unique module identifier. Prefer setting `manifest['name']`."""
        if self.manifest and "name" in self.manifest:
            return str(self.manifest["name"])
        raise NotImplementedError(f"{type(self).__name__} must set `manifest` or override `name`")

    @property
    def version(self) -> str:
        """Semver string. Prefer setting `manifest['version']`."""
        if self.manifest and "version" in self.manifest:
            return str(self.manifest["version"])
        raise NotImplementedError(
            f"{type(self).__name__} must set `manifest` or override `version`"
        )

    @property
    def dependencies(self) -> list[str]:
        """List of required module names that must be loaded first."""
        if self.manifest and "depends" in self.manifest:
            return list(self.manifest.get("depends") or [])
        return []

    # --- Core contract ---------------------------------------------------

    @abstractmethod
    def get_models(self) -> list[type[DeclarativeBase]]:
        """Return SQLAlchemy models to register with the database."""

    @abstractmethod
    def get_router(self) -> APIRouter:
        """Return FastAPI router to mount at ``/api/v1/{module_name}/``."""

    def get_event_handlers(self) -> dict[str, Callable[..., Any]]:
        """Return map of event_name -> handler function.

        Handlers receive event data as a dict (and optionally a DB session
        when async). They should not return anything.
        """
        return {}

    def get_permissions(self) -> list[str]:
        """Return custom permissions this module adds to RBAC.

        Format: ``'resource.action'`` (no module prefix). The registry
        namespaces them automatically, e.g. ``'patients.read'`` from
        ``clinical`` becomes ``'clinical.patients.read'``.
        """
        return []

    # --- AI agent contract ----------------------------------------------

    @abstractmethod
    def get_tools(self) -> list[Tool]:
        """Return callable actions this module exposes to AI agents.

        Return ``[]`` if the module does not expose any tools yet. Tool
        names are namespaced automatically: a tool named
        ``create_appointment`` from module ``agenda`` is registered as
        ``agenda.create_appointment`` in the global
        :class:`~app.core.agents.tools.registry.ToolRegistry`.

        Every new write-capable module MUST eventually expose its
        mutating service methods here so AI agents can invoke them
        through the audited chokepoint rather than calling service
        functions directly. See ``docs/creating-modules.md`` for the
        full contract.
        """

    def get_agents(self) -> list[type[BaseAgent]]:
        """Return :class:`~app.core.agents.base.BaseAgent` subclasses
        this module registers.

        Default is an empty list. Override only if the module ships
        agents itself (as opposed to merely exposing tools).
        """
        return []

    # --- Lifecycle hooks (v1 defaults are no-ops) ------------------------

    async def install(self, ctx: ModuleContext) -> None:
        """Called on first install after migrations ran.

        Typical use: load ``data/*.yaml`` seed files, provision data.
        """

    async def uninstall(self, ctx: ModuleContext) -> None:
        """Called before Alembic downgrade and data removal.

        Typical use: clean up external resources, stop background tasks.
        """

    async def post_upgrade(self, ctx: ModuleContext, from_version: str) -> None:
        """Called after migrations when upgrading to a newer version.

        Typical use: re-run seeds with new ``noupdate`` flags, backfill.
        """

    # --- Manifest accessor ----------------------------------------------

    def get_manifest(self) -> Manifest:
        """Return the parsed manifest, synthesizing one from legacy props
        if the class does not declare one.

        Modules that subclass :class:`BaseModule` without a ``manifest``
        class attribute (legacy code path) get a minimal manifest with
        ``name``/``version``/``depends`` populated from their properties.
        """
        if self.manifest:
            return Manifest.from_dict(self.manifest)

        return Manifest.from_dict(
            {
                "name": self.name,
                "version": self.version,
                "depends": list(self.dependencies),
                "summary": "",
                "category": "official",
                "installable": True,
                "auto_install": True,
                "removable": False,
            }
        )
