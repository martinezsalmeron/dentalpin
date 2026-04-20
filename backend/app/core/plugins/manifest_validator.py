"""Opinionated manifest validation used by both pytest and CI.

``Manifest.from_dict`` already rejects missing required keys and bad
categories. This module layers **ecosystem-level** checks on top:

* semver-ish ``version`` (``X.Y.Z``)
* ``min_core_version`` is also semver-ish when present
* every role in ``role_permissions`` is a known RBAC role
* every permission string in ``role_permissions`` is either ``"*"`` or
  declared in ``module.get_permissions()``
* every navigation ``permission`` is namespaced (``<module>.<perm>``)
* ``depends`` contains only known module names, if caller provides them

The validator returns a list of :class:`ValidationIssue` rather than
raising, so callers can summarise them (pytest) or print them (CI).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.core.auth.permissions import ROLES

from .manifest import ManifestError

if TYPE_CHECKING:
    from .base import BaseModule


SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")


@dataclass(frozen=True)
class ValidationIssue:
    module_name: str
    code: str
    message: str


def validate_module(
    module: BaseModule,
    *,
    known_module_names: set[str] | None = None,
) -> list[ValidationIssue]:
    """Return every issue found in ``module``'s manifest.

    ``known_module_names`` is used to validate ``depends`` references.
    Pass ``None`` to skip that particular check.
    """
    issues: list[ValidationIssue] = []

    try:
        manifest = module.get_manifest()
    except ManifestError as exc:
        issues.append(
            ValidationIssue(
                module_name=getattr(module, "name", "?"),
                code="MANIFEST_SCHEMA",
                message=str(exc),
            )
        )
        return issues

    name = manifest.name

    if not SEMVER_RE.match(manifest.version):
        issues.append(
            ValidationIssue(
                module_name=name,
                code="VERSION_FORMAT",
                message=f"version '{manifest.version}' is not semver-ish (X.Y.Z)",
            )
        )

    if manifest.min_core_version and not SEMVER_RE.match(manifest.min_core_version):
        issues.append(
            ValidationIssue(
                module_name=name,
                code="MIN_CORE_VERSION_FORMAT",
                message=(f"min_core_version '{manifest.min_core_version}' is not semver-ish"),
            )
        )

    declared_perms = set(module.get_permissions())
    valid_roles = set(ROLES)

    for role, perms in manifest.role_permissions.items():
        if role not in valid_roles:
            issues.append(
                ValidationIssue(
                    module_name=name,
                    code="UNKNOWN_ROLE",
                    message=f"role_permissions mentions unknown role '{role}'",
                )
            )
            continue

        for perm in perms:
            if perm == "*":
                continue
            # Trailing wildcard such as "plans.*": require at least one
            # declared permission under that prefix.
            if perm.endswith(".*"):
                prefix = perm[:-1]
                if not any(d.startswith(prefix) for d in declared_perms):
                    issues.append(
                        ValidationIssue(
                            module_name=name,
                            code="UNKNOWN_PERMISSION",
                            message=(
                                f"role '{role}' grants '{perm}' but no "
                                f"declared permission starts with '{prefix}'"
                            ),
                        )
                    )
                continue
            if perm not in declared_perms:
                issues.append(
                    ValidationIssue(
                        module_name=name,
                        code="UNKNOWN_PERMISSION",
                        message=(
                            f"role '{role}' grants '{perm}' which is not in "
                            f"get_permissions(): {sorted(declared_perms)}"
                        ),
                    )
                )

    for item in manifest.frontend.get("navigation") or []:
        perm = item.get("permission")
        if perm and "." not in perm:
            issues.append(
                ValidationIssue(
                    module_name=name,
                    code="NAV_PERM_NOT_NAMESPACED",
                    message=(
                        f"navigation to={item.get('to')} uses permission "
                        f"'{perm}' without a module prefix"
                    ),
                )
            )

    if known_module_names is not None:
        for dep in manifest.depends:
            if dep not in known_module_names:
                issues.append(
                    ValidationIssue(
                        module_name=name,
                        code="UNKNOWN_DEPENDENCY",
                        message=f"depends on unknown module '{dep}'",
                    )
                )

    return issues


def validate_modules(modules: list[BaseModule]) -> list[ValidationIssue]:
    """Run :func:`validate_module` across a set of modules.

    Aggregates ``depends`` references against the set of known names
    (the modules passed in) so missing deps surface here even when a
    single-module check wouldn't catch them.
    """
    known = {m.name for m in modules}
    issues: list[ValidationIssue] = []
    for module in modules:
        issues.extend(validate_module(module, known_module_names=known))
    return issues
