"""Module manifest schema.

Modules declare metadata through a `MANIFEST` dict. The manifest is the
source of truth for identity (name, version), compatibility
(`min_core_version`), dependencies, policies (installable, removable,
auto_install), seed data files, role-permission seeds and frontend
navigation items.

Validation is intentionally lenient in v1: only required keys are checked.
Optional keys default to safe values. Unknown keys are preserved.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .state import ModuleCategory

REQUIRED_KEYS = ("name", "version")


@dataclass(frozen=True)
class Manifest:
    """Parsed, validated manifest for a module.

    Construction happens via :meth:`from_dict`, which applies defaults and
    raises :class:`ManifestError` for schema violations.
    """

    name: str
    version: str
    summary: str = ""
    author: str = ""
    license: str = ""
    category: ModuleCategory = ModuleCategory.OFFICIAL
    min_core_version: str | None = None
    max_core_version: str | None = None
    depends: tuple[str, ...] = ()
    installable: bool = True
    auto_install: bool = True
    removable: bool = True
    data_files: tuple[str, ...] = ()
    role_permissions: dict[str, tuple[str, ...]] = field(default_factory=dict)
    frontend: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Manifest:
        """Parse a manifest dict, validate required keys, apply defaults."""
        missing = [k for k in REQUIRED_KEYS if not data.get(k)]
        if missing:
            raise ManifestError(f"Manifest missing required keys: {missing}")

        category_raw = data.get("category", ModuleCategory.OFFICIAL)
        try:
            category = ModuleCategory(category_raw)
        except ValueError as exc:
            raise ManifestError(
                f"Invalid category '{category_raw}' for module '{data['name']}'. "
                f"Must be one of: {[c.value for c in ModuleCategory]}"
            ) from exc

        role_permissions_raw = data.get("role_permissions") or {}
        if not isinstance(role_permissions_raw, dict):
            raise ManifestError(f"role_permissions must be a dict for module '{data['name']}'")
        role_permissions = {role: tuple(perms) for role, perms in role_permissions_raw.items()}

        return cls(
            name=str(data["name"]),
            version=str(data["version"]),
            summary=str(data.get("summary", "")),
            author=str(data.get("author", "")),
            license=str(data.get("license", "")),
            category=category,
            min_core_version=data.get("min_core_version"),
            max_core_version=data.get("max_core_version"),
            depends=tuple(data.get("depends") or ()),
            installable=bool(data.get("installable", True)),
            auto_install=bool(data.get("auto_install", True)),
            removable=bool(data.get("removable", True)),
            data_files=tuple(data.get("data_files") or ()),
            role_permissions=role_permissions,
            frontend=dict(data.get("frontend") or {}),
        )

    def to_snapshot(self) -> dict[str, Any]:
        """Return a JSON-serializable snapshot for persistence."""
        return {
            "name": self.name,
            "version": self.version,
            "summary": self.summary,
            "author": self.author,
            "license": self.license,
            "category": self.category.value,
            "min_core_version": self.min_core_version,
            "max_core_version": self.max_core_version,
            "depends": list(self.depends),
            "installable": self.installable,
            "auto_install": self.auto_install,
            "removable": self.removable,
            "data_files": list(self.data_files),
            "role_permissions": {
                role: list(perms) for role, perms in self.role_permissions.items()
            },
            "frontend": self.frontend,
        }


class ManifestError(ValueError):
    """Raised when a manifest fails validation."""
