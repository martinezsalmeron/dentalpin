"""Unit tests for manifest parsing and validation."""

from __future__ import annotations

import pytest

from app.core.plugins.manifest import Manifest, ManifestError
from app.core.plugins.state import ModuleCategory


def test_manifest_defaults() -> None:
    m = Manifest.from_dict({"name": "foo", "version": "1.0.0"})
    assert m.name == "foo"
    assert m.version == "1.0.0"
    assert m.category == ModuleCategory.OFFICIAL
    assert m.installable is True
    assert m.auto_install is True
    assert m.removable is True
    assert m.depends == ()
    assert m.role_permissions == {}


def test_manifest_full_payload() -> None:
    payload = {
        "name": "billing",
        "version": "1.2.3",
        "summary": "Invoicing",
        "author": "Core team",
        "license": "BSL-1.1",
        "category": "official",
        "min_core_version": "1.0.0",
        "depends": ["clinical", "catalog"],
        "installable": True,
        "auto_install": False,
        "removable": False,
        "data_files": ["data/taxes.yaml"],
        "role_permissions": {
            "dentist": ["invoices.read", "invoices.write"],
            "receptionist": ["invoices.read"],
        },
        "frontend": {"navigation": [{"label": "nav.billing"}]},
    }

    m = Manifest.from_dict(payload)

    assert m.name == "billing"
    assert m.version == "1.2.3"
    assert m.depends == ("clinical", "catalog")
    assert m.data_files == ("data/taxes.yaml",)
    assert m.role_permissions["dentist"] == ("invoices.read", "invoices.write")
    assert m.frontend["navigation"][0]["label"] == "nav.billing"
    assert m.auto_install is False
    assert m.removable is False


def test_manifest_missing_required_keys() -> None:
    with pytest.raises(ManifestError):
        Manifest.from_dict({"name": "foo"})

    with pytest.raises(ManifestError):
        Manifest.from_dict({"version": "1.0.0"})


def test_manifest_invalid_category() -> None:
    with pytest.raises(ManifestError):
        Manifest.from_dict({"name": "foo", "version": "1", "category": "enterprise"})


def test_manifest_invalid_role_permissions_type() -> None:
    with pytest.raises(ManifestError):
        Manifest.from_dict({"name": "foo", "version": "1", "role_permissions": ["bad"]})


def test_manifest_community_category() -> None:
    m = Manifest.from_dict({"name": "foo", "version": "1", "category": "community"})
    assert m.category == ModuleCategory.COMMUNITY


def test_manifest_snapshot_roundtrip() -> None:
    payload = {
        "name": "foo",
        "version": "1.0.0",
        "depends": ["bar"],
        "role_permissions": {"dentist": ["read"]},
    }
    m = Manifest.from_dict(payload)
    snap = m.to_snapshot()

    assert snap["depends"] == ["bar"]
    assert snap["role_permissions"] == {"dentist": ["read"]}
    # Round-trip preserves structure.
    restored = Manifest.from_dict(snap)
    assert restored.name == m.name
    assert restored.depends == m.depends
    assert restored.role_permissions == m.role_permissions
