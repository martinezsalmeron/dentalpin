"""Consistency tests for declared manifests vs ROLE_PERMISSIONS.

Every module now ships a ``manifest`` dict. This file asserts that:

* every module's manifest is schema-valid;
* every permission a module declares via ``get_permissions()`` shows up
  in its manifest's ``role_permissions`` (admin's ``*`` counts as
  covering everything);
* for each role + module, the permissions listed in the manifest
  produce the same *effective* set as the legacy ``ROLE_PERMISSIONS``
  table in ``app.core.auth.permissions``.

The legacy table stays authoritative in Fase A — these tests exist so
that, when it is replaced by the manifest-driven aggregator, drift is
caught before the swap.
"""

from __future__ import annotations

import pytest

from app.core.auth.permissions import ROLE_PERMISSIONS, has_permission
from app.core.plugins.loader import discover_modules

MODULE_NAMES = {
    "patients",
    "patients_clinical",
    "agenda",
    "patient_timeline",
    "catalog",
    "budget",
    "billing",
    "odontogram",
    "treatment_plan",
    "media",
    "notifications",
    "reports",
}


@pytest.fixture(scope="module")
def modules():
    by_name = {m.name: m for m in discover_modules()}
    missing = MODULE_NAMES - by_name.keys()
    assert not missing, f"modules missing from discovery: {missing}"
    return by_name


def test_every_module_has_valid_manifest(modules) -> None:
    for name, module in modules.items():
        manifest = module.get_manifest()
        assert manifest.name == name
        assert manifest.version
        assert manifest.author
        assert manifest.license
        assert manifest.category.value == "official"
        assert manifest.role_permissions  # at least admin


def test_manifest_permissions_covered_by_module_get_permissions(modules) -> None:
    """Every non-wildcard perm in role_permissions must exist in the
    module's own ``get_permissions()`` output."""
    for name, module in modules.items():
        declared = set(module.get_permissions())
        manifest = module.get_manifest()
        for role, perms in manifest.role_permissions.items():
            for perm in perms:
                if perm == "*":
                    continue
                assert perm in declared, (
                    f"{name}: role '{role}' grants '{perm}' but module "
                    f"does not declare it. declared={sorted(declared)}"
                )


def test_manifest_matches_legacy_role_table(modules) -> None:
    """Expanding each manifest's role_permissions (with module prefix)
    must yield the same namespaced permission set that
    ``has_permission`` already honours for that role."""
    for role in ROLE_PERMISSIONS:
        if role == "admin":
            continue  # admin has '*' everywhere by contract
        for module_name, module in modules.items():
            manifest_perms = _expand_manifest_perms(module, role)
            for perm in module.get_permissions():
                namespaced = f"{module_name}.{perm}"
                legacy_grants = has_permission(role, namespaced)
                manifest_grants = _manifest_grants(manifest_perms, perm)
                assert legacy_grants == manifest_grants, (
                    f"{role} × {namespaced}: legacy={legacy_grants} "
                    f"manifest={manifest_grants} "
                    f"(manifest perms for module={manifest_perms})"
                )


def _expand_manifest_perms(module, role: str) -> list[str]:
    manifest = module.get_manifest()
    return list(manifest.role_permissions.get(role, ()))


def _manifest_grants(role_perms: list[str], module_perm: str) -> bool:
    """Replicate wildcard resolution against a module-local permission."""
    if "*" in role_perms:
        return True
    for perm in role_perms:
        if perm == module_perm:
            return True
        # support sub-wildcards like "plans.*"
        if perm.endswith(".*") and module_perm.startswith(perm[:-1]):
            return True
    return False
