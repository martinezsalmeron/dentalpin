"""Single-tenant resolver for self-hosted deployments.

Reads ``DATABASE_URL`` and the ``ModuleRegistry`` exactly once at
construction time and returns the same ``TenantContext`` on every call.
O(1), no network, no cache (precomputed).
"""

from __future__ import annotations

import logging

from starlette.requests import Request

from app.config import settings
from app.core.plugins.registry import module_registry

from .context import TenantContext

logger = logging.getLogger(__name__)

DEFAULT_TENANT_SLUG = "default"


class SingleTenantResolver:
    """Resolver that always returns the same tenant.

    The tenant is built once from ``settings.DATABASE_URL`` and the set of
    modules currently loaded in the ``ModuleRegistry``. Subsequent
    ``resolve()`` / ``resolve_by_slug()`` calls return the cached instance.
    """

    def __init__(self) -> None:
        self._context = TenantContext(
            slug=DEFAULT_TENANT_SLUG,
            db_url=settings.DATABASE_URL,
            storage_prefix="",
            modules_enabled=frozenset(module.name for module in module_registry.list_modules()),
        )

    async def resolve(self, request: Request) -> TenantContext:
        logger.debug("SingleTenantResolver.resolve ignoring request")
        return self._context

    async def resolve_by_slug(self, slug: str) -> TenantContext:
        if slug != DEFAULT_TENANT_SLUG:
            raise LookupError(f"Unknown tenant slug: {slug!r}")
        return self._context
