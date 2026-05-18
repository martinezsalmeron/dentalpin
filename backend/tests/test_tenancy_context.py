"""Tests for ``TenantContext`` (multi-tenancy Fase 1)."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from types import MappingProxyType

import pytest

from app.core.tenancy import TenantContext


def _base_kwargs() -> dict[str, object]:
    return {
        "slug": "default",
        "db_url": "postgresql+asyncpg://user:pass@localhost/test",
    }


class TestTenantContextConstruction:
    def test_minimum_fields_ok(self) -> None:
        ctx = TenantContext(**_base_kwargs())
        assert ctx.slug == "default"
        assert ctx.storage_prefix == ""
        assert ctx.modules_enabled == frozenset()
        assert ctx.metadata == {}

    def test_empty_db_url_raises(self) -> None:
        with pytest.raises(ValueError, match="db_url cannot be empty"):
            TenantContext(slug="default", db_url="")

    def test_metadata_wrapped_in_mappingproxy(self) -> None:
        ctx = TenantContext(**_base_kwargs(), metadata={"plan": "pro"})
        assert isinstance(ctx.metadata, MappingProxyType)
        assert ctx.metadata["plan"] == "pro"

    def test_metadata_default_is_mappingproxy(self) -> None:
        ctx = TenantContext(**_base_kwargs())
        assert isinstance(ctx.metadata, MappingProxyType)


class TestTenantContextImmutability:
    def test_frozen_blocks_mutation(self) -> None:
        ctx = TenantContext(**_base_kwargs())
        with pytest.raises(FrozenInstanceError):
            ctx.slug = "other"  # type: ignore[misc]

    def test_metadata_proxy_blocks_write(self) -> None:
        ctx = TenantContext(**_base_kwargs(), metadata={"plan": "pro"})
        with pytest.raises(TypeError):
            ctx.metadata["plan"] = "free"  # type: ignore[index]


class TestTenantContextValueSemantics:
    def test_equal_when_fields_match(self) -> None:
        a = TenantContext(**_base_kwargs(), modules_enabled=frozenset({"patients"}))
        b = TenantContext(**_base_kwargs(), modules_enabled=frozenset({"patients"}))
        assert a == b

    def test_hashable_goes_in_set(self) -> None:
        a = TenantContext(**_base_kwargs())
        b = TenantContext(**_base_kwargs())
        assert {a, b} == {a}


class TestWithMetadata:
    def test_extends_metadata(self) -> None:
        ctx = TenantContext(**_base_kwargs(), metadata={"plan": "pro"})
        extended = ctx.with_metadata(cluster_id="eu-1")
        assert extended.metadata["plan"] == "pro"
        assert extended.metadata["cluster_id"] == "eu-1"

    def test_overrides_existing_key(self) -> None:
        ctx = TenantContext(**_base_kwargs(), metadata={"plan": "pro"})
        extended = ctx.with_metadata(plan="enterprise")
        assert extended.metadata["plan"] == "enterprise"

    def test_does_not_mutate_original(self) -> None:
        ctx = TenantContext(**_base_kwargs(), metadata={"plan": "pro"})
        ctx.with_metadata(cluster_id="eu-1")
        assert "cluster_id" not in ctx.metadata

    def test_returns_new_mappingproxy(self) -> None:
        ctx = TenantContext(**_base_kwargs())
        extended = ctx.with_metadata(plan="free")
        assert isinstance(extended.metadata, MappingProxyType)
