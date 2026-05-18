"""Tenant resolver Protocol.

Implementations decide, given a request or a slug, which ``TenantContext``
applies. Self-hosted uses ``SingleTenantResolver``; a future SaaS module
will provide its own implementation that swaps the resolver registered on
``app.state.tenant_resolver`` at startup.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from starlette.requests import Request

from .context import TenantContext


@runtime_checkable
class TenantResolver(Protocol):
    """Protocol for resolving the current tenant.

    Implementations MUST raise ``LookupError`` (not an HTTP exception) when
    a slug is unknown. Callers in the HTTP layer are responsible for
    translating that into a 404 if appropriate.
    """

    async def resolve(self, request: Request) -> TenantContext:
        """Resolve the tenant for an incoming HTTP request."""
        ...

    async def resolve_by_slug(self, slug: str) -> TenantContext:
        """Resolve a tenant by slug (background jobs, CLI, tests)."""
        ...
