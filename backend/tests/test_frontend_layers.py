"""Tests for the frontend_layers helper + fixture community module."""

from __future__ import annotations

import json
from pathlib import Path

from app.core.plugins.frontend_layers import (
    MODULES_JSON_SCHEMA_VERSION,
    LayerEntry,
    build_payload,
    collect_layers,
    read_modules_json,
    resolve_layer_path,
    write_modules_json,
)
from tests.fixtures.sample_module import SampleModule


def test_resolve_layer_path_for_fixture() -> None:
    module = SampleModule()
    path = resolve_layer_path(module)
    assert path is not None
    assert path.name == "frontend"
    assert (path / "nuxt.config.ts").exists()


def test_resolve_layer_path_returns_none_for_module_without_layer() -> None:
    from app.modules.billing import BillingModule

    # BillingModule has no ``frontend/`` directory yet (moves to a layer
    # in Fase B.6). ``resolve_layer_path`` must return ``None`` for any
    # such module until then.
    assert resolve_layer_path(BillingModule()) is None


def test_collect_layers_filters_modules_without_layer() -> None:
    from app.modules.billing import BillingModule

    layers = collect_layers([BillingModule(), SampleModule()])
    assert len(layers) == 1
    assert layers[0].module_name == "sample_community"


def test_build_payload_shape() -> None:
    entries = [LayerEntry(module_name="foo", path="/abs/foo/frontend")]
    payload = build_payload(entries)
    assert payload["version"] == MODULES_JSON_SCHEMA_VERSION
    assert payload["layers"] == ["/abs/foo/frontend"]
    assert payload["modules"] == [{"name": "foo", "path": "/abs/foo/frontend"}]


def test_write_modules_json_is_atomic_and_idempotent(tmp_path: Path) -> None:
    entries = [LayerEntry(module_name="sample", path=str(tmp_path / "layer"))]
    target = write_modules_json(entries, frontend_root=tmp_path)
    assert target == tmp_path / "modules.json"

    payload = json.loads(target.read_text())
    assert payload["layers"] == [str(tmp_path / "layer")]
    assert (tmp_path / "modules.json.tmp").exists() is False

    # Second write with no entries rewrites atomically.
    write_modules_json([], frontend_root=tmp_path)
    payload = json.loads(target.read_text())
    assert payload["layers"] == []


def test_read_modules_json_missing_file_returns_empty(tmp_path: Path) -> None:
    payload = read_modules_json(frontend_root=tmp_path)
    assert payload["layers"] == []
    assert payload["version"] == MODULES_JSON_SCHEMA_VERSION


def test_read_modules_json_tolerates_malformed(tmp_path: Path) -> None:
    (tmp_path / "modules.json").write_text("not json {")
    payload = read_modules_json(frontend_root=tmp_path)
    assert payload["layers"] == []
