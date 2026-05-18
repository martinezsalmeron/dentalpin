"""Tests for ``SingleTenantResolver`` (multi-tenancy Fase 1)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from starlette.requests import Request

from app.core.tenancy import SingleTenantResolver, TenantContext, TenantResolver
from app.core.tenancy.single import DEFAULT_TENANT_SLUG


@pytest.fixture
def fake_request() -> Request:
    """Minimal ASGI scope; the resolver never actually inspects it."""
    return Request(scope={"type": "http", "headers": []})


@pytest.fixture
def resolver(monkeypatch: pytest.MonkeyPatch) -> SingleTenantResolver:
    """Build a resolver with the registry mocked to a known module set.

    Keeps the assertion stable regardless of how many modules conftest
    happens to load.
    """
    m1 = MagicMock()
    m1.name = "patients"
    m2 = MagicMock()
    m2.name = "agenda"
    fake_registry = MagicMock()
    fake_registry.list_modules.return_value = [m1, m2]
    monkeypatch.setattr("app.core.tenancy.single.module_registry", fake_registry)
    return SingleTenantResolver()


class TestResolve:
    @pytest.mark.asyncio
    async def test_returns_tenant_context(
        self, resolver: SingleTenantResolver, fake_request: Request
    ) -> None:
        ctx = await resolver.resolve(fake_request)
        assert isinstance(ctx, TenantContext)
        assert ctx.slug == DEFAULT_TENANT_SLUG

    @pytest.mark.asyncio
    async def test_returns_same_instance_each_call(
        self, resolver: SingleTenantResolver, fake_request: Request
    ) -> None:
        a = await resolver.resolve(fake_request)
        b = await resolver.resolve(fake_request)
        assert a is b

    @pytest.mark.asyncio
    async def test_modules_enabled_from_registry(
        self, resolver: SingleTenantResolver, fake_request: Request
    ) -> None:
        ctx = await resolver.resolve(fake_request)
        assert ctx.modules_enabled == frozenset({"patients", "agenda"})


class TestResolveBySlug:
    @pytest.mark.asyncio
    async def test_default_slug_works(self, resolver: SingleTenantResolver) -> None:
        ctx = await resolver.resolve_by_slug(DEFAULT_TENANT_SLUG)
        assert ctx.slug == DEFAULT_TENANT_SLUG

    @pytest.mark.asyncio
    async def test_unknown_slug_raises_lookuperror(self, resolver: SingleTenantResolver) -> None:
        with pytest.raises(LookupError, match="Unknown tenant slug"):
            await resolver.resolve_by_slug("other")

    @pytest.mark.asyncio
    async def test_default_and_resolve_return_same(
        self, resolver: SingleTenantResolver, fake_request: Request
    ) -> None:
        via_request = await resolver.resolve(fake_request)
        via_slug = await resolver.resolve_by_slug(DEFAULT_TENANT_SLUG)
        assert via_request is via_slug


class TestProtocolConformance:
    def test_satisfies_runtime_protocol(self, resolver: SingleTenantResolver) -> None:
        assert isinstance(resolver, TenantResolver)
