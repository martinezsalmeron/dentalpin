#!/usr/bin/env python3
"""Coverage check for the documentation portal (ADR 0009 / issue #75).

For every module under ``backend/app/modules/<name>/``, verifies that
the documentation contract holds:

- ``docs/technical/<module>/overview.md`` exists.
- ``docs/technical/<module>/permissions.md`` exists when the module
  returns at least one permission from ``get_permissions()``.
- ``docs/technical/<module>/events.md`` exists when the module emits or
  subscribes events.
- Every Nuxt page under ``<module>/frontend/pages/**`` has a matching
  screen file in **both**
  ``docs/user-manual/en/<module>/screens/<slug>.md`` *and*
  ``docs/user-manual/es/<module>/screens/<slug>.md`` with frontmatter
  whose ``route`` field equals the page's route.
- Every screen file's frontmatter ``route`` resolves to a real page,
  ``related_endpoints`` (if present) reference paths that exist on the
  module's router, and ``related_permissions`` (if present) are
  returned by the module's ``get_permissions()`` (with the namespace
  prefix stripped or left as-is).

Default mode is **warning-only** (prints findings, exits 0). The
``--strict`` flag turns violations into an exit code 1 and is what the
backfill PR will switch CI to. Today, the warning-only mode runs in the
existing ``catalog-freshness`` CI job.

Companion to ``backend/scripts/generate_catalogs.py``. Shares its
bootstrap, but does **not** mutate any file.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

def _locate_repo_root() -> Path:
    """Resolve the repo root.

    Order:

    1. ``DENTALPIN_REPO_ROOT`` env var if set (useful in Docker where
       ``/app`` is the backend mount and ``/docs`` is mounted separately —
       set ``DENTALPIN_REPO_ROOT=/`` and ensure both ``/docs`` and
       ``/backend`` exist as symlinks or mounts).
    2. Walk up from this file until we find both ``docs/`` and ``backend/``.

    Works on the GitHub Actions runner (host layout), and in Docker when
    the env var is set.
    """
    override = os.environ.get("DENTALPIN_REPO_ROOT")
    if override:
        root = Path(override).resolve()
        if (root / "docs").is_dir() and (root / "backend").is_dir():
            return root
        raise RuntimeError(
            f"DENTALPIN_REPO_ROOT={override!r} but it doesn't contain "
            "both `docs/` and `backend/`."
        )
    here = Path(__file__).resolve()
    for candidate in (here.parent, *here.parents):
        if (candidate / "docs").is_dir() and (candidate / "backend").is_dir():
            return candidate
    raise RuntimeError(
        f"Could not locate repo root from {here}. "
        "Set DENTALPIN_REPO_ROOT or run the script from a checkout that "
        "contains both `docs/` and `backend/`."
    )


REPO_ROOT = _locate_repo_root()
BACKEND_ROOT = REPO_ROOT / "backend"
MODULES_ROOT = BACKEND_ROOT / "app" / "modules"
DOCS_ROOT = REPO_ROOT / "docs"
TECHNICAL_ROOT = DOCS_ROOT / "technical"
USER_MANUAL_ROOT = DOCS_ROOT / "user-manual"

LOCALES = ("en", "es")


def _bootstrap_env() -> None:
    os.environ.setdefault(
        "DATABASE_URL",
        "postgresql+asyncpg://stub:stub@localhost:5432/stub",
    )
    os.environ.setdefault("SECRET_KEY", "docs-coverage-stub-key-32chars-minimum")
    os.environ.setdefault("ENVIRONMENT", "test")
    os.environ.setdefault("TESTING", "true")
    os.environ.setdefault("DENTALPIN_DEV_MODULE_SCAN", "true")
    sys.path.insert(0, str(BACKEND_ROOT))


_bootstrap_env()

from app.core.plugins.loader import discover_modules  # noqa: E402

# ---------------------------------------------------------------------------
# Tiny YAML frontmatter parser.
#
# We deliberately avoid pulling in PyYAML — the schema is fixed (strings,
# lists of strings) and a regex split is enough. If the contract grows
# nested objects, swap this for `yaml.safe_load`.
# ---------------------------------------------------------------------------


def _parse_frontmatter(text: str) -> dict[str, object]:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    body = text[3:end].strip("\n")
    out: dict[str, object] = {}
    current_list_key: str | None = None
    for raw in body.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw.startswith("  - "):
            if current_list_key is None:
                continue
            out.setdefault(current_list_key, [])
            assert isinstance(out[current_list_key], list)
            out[current_list_key].append(raw.removeprefix("  - ").strip())
            continue
        if raw.startswith("- "):  # top-level list — not in our schema
            continue
        if ":" not in raw:
            continue
        key, _, value = raw.partition(":")
        key = key.strip()
        value = value.strip()
        if value == "":
            current_list_key = key
            out[key] = []
        else:
            current_list_key = None
            out[key] = value.strip("\"'")
    return out


# ---------------------------------------------------------------------------
# Module discovery + per-module facts
# ---------------------------------------------------------------------------


@dataclass
class ModuleFacts:
    name: str
    permissions: list[str]
    events_emitted: list[str]
    events_consumed: list[str]
    pages: dict[str, Path]                # route -> .vue path
    endpoints: list[tuple[str, str]]      # (METHOD, full path including /api/v1/<m>)
    has_frontend: bool


HTTP_METHODS = ("get", "post", "put", "patch", "delete")
ROUTER_DECORATOR_RE = re.compile(
    r"@router\.(?P<method>get|post|put|patch|delete)\(\s*[\"'](?P<path>[^\"']*)[\"']",
)
PUBLISH_RE = re.compile(
    r"event_bus\.publish\(\s*(?:EventType\.[A-Z_]+|[\"'](?P<lit>[\w.]+)[\"'])"
)


def _scan_module_endpoints(mod_dir: Path, mount_prefix: str) -> list[tuple[str, str]]:
    """Return [(METHOD, '/api/v1/<m>/<path>')] for every router decorator."""
    endpoints: list[tuple[str, str]] = []
    for py_file in mod_dir.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8", errors="replace")
        if "@router." not in text:
            continue
        for match in ROUTER_DECORATOR_RE.finditer(text):
            method = match.group("method").upper()
            sub_path = match.group("path") or ""
            full = f"{mount_prefix}{sub_path}".rstrip("/") or mount_prefix
            endpoints.append((method, full))
    return endpoints


def _scan_module_publishers(mod_dir: Path) -> set[str]:
    """Best-effort grep of event_bus.publish callsites in the module."""
    out: set[str] = set()
    for py_file in mod_dir.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8", errors="replace")
        if "event_bus.publish" not in text:
            continue
        for match in PUBLISH_RE.finditer(text):
            lit = match.group("lit")
            if lit:
                out.add(lit)
    return out


def _page_to_route(rel: Path) -> str:
    """Convert pages/foo/[id].vue → /foo/[id], pages/foo/index.vue → /foo."""
    parts = list(rel.with_suffix("").parts)
    if parts and parts[-1] == "index":
        parts.pop()
    return "/" + "/".join(parts) if parts else "/"


def _scan_module_pages(mod_dir: Path) -> dict[str, Path]:
    pages_dir = mod_dir / "frontend" / "pages"
    out: dict[str, Path] = {}
    if not pages_dir.is_dir():
        return out
    for vue in pages_dir.rglob("*.vue"):
        rel = vue.relative_to(pages_dir)
        route = _page_to_route(rel)
        out[route] = vue
    return out


def _collect_facts(module) -> ModuleFacts:
    name = module.name
    mod_dir = MODULES_ROOT / name
    permissions = list(getattr(module, "get_permissions", lambda: [])() or [])
    handlers = getattr(module, "get_event_handlers", lambda: {})() or {}
    events_consumed = sorted(handlers.keys())
    events_emitted = sorted(_scan_module_publishers(mod_dir))
    pages = _scan_module_pages(mod_dir)
    endpoints = _scan_module_endpoints(mod_dir, mount_prefix=f"/api/v1/{name}")
    has_frontend = (mod_dir / "frontend").is_dir()
    return ModuleFacts(
        name=name,
        permissions=permissions,
        events_emitted=events_emitted,
        events_consumed=events_consumed,
        pages=pages,
        endpoints=endpoints,
        has_frontend=has_frontend,
    )


# ---------------------------------------------------------------------------
# Screen MD discovery
# ---------------------------------------------------------------------------


@dataclass
class ScreenDoc:
    locale: str                # 'en' | 'es'
    module: str
    path: Path
    frontmatter: dict[str, object]


def _collect_screens(module: str) -> dict[str, list[ScreenDoc]]:
    """{locale: [ScreenDoc, ...]} for every screen MD found for this module."""
    out: dict[str, list[ScreenDoc]] = {loc: [] for loc in LOCALES}
    for locale in LOCALES:
        screens_dir = USER_MANUAL_ROOT / locale / module / "screens"
        if not screens_dir.is_dir():
            continue
        for md in sorted(screens_dir.glob("*.md")):
            text = md.read_text(encoding="utf-8", errors="replace")
            fm = _parse_frontmatter(text)
            out[locale].append(
                ScreenDoc(locale=locale, module=module, path=md, frontmatter=fm)
            )
    return out


# ---------------------------------------------------------------------------
# The actual checks
# ---------------------------------------------------------------------------


@dataclass
class Findings:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def err(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def ok(self) -> bool:
        return not self.errors and not self.warnings


def _normalise_endpoint(method: str, path: str) -> str:
    """`{patient_id}` and `:patient_id` and `[id]` all collapse to `<param>`."""
    norm = re.sub(r"\{[^}]+\}", "<param>", path)
    norm = re.sub(r":[a-zA-Z_][\w]*", "<param>", norm)
    norm = re.sub(r"\[[^\]]+\]", "<param>", norm)
    return f"{method.upper()} {norm.rstrip('/') or '/'}"


def _check_module(facts: ModuleFacts, findings: Findings) -> None:
    name = facts.name
    tech_dir = TECHNICAL_ROOT / name

    # 1. technical/overview.md
    if not (tech_dir / "overview.md").is_file():
        findings.err(
            f"{name}: missing docs/technical/{name}/overview.md "
            "(every module needs a technical overview)."
        )

    # 2. technical/permissions.md when permissions exist
    if facts.permissions and not (tech_dir / "permissions.md").is_file():
        findings.err(
            f"{name}: get_permissions() returns {facts.permissions!r} "
            f"but docs/technical/{name}/permissions.md is missing."
        )

    # 3. technical/events.md when events flow either way
    if (facts.events_emitted or facts.events_consumed) and not (tech_dir / "events.md").is_file():
        findings.err(
            f"{name}: emits/subscribes events "
            f"(emit={facts.events_emitted}, sub={facts.events_consumed}) "
            f"but docs/technical/{name}/events.md is missing."
        )

    # 4. Per-screen coverage in BOTH locales.
    screens_by_locale = _collect_screens(name)
    routes_by_locale = {
        locale: {str(s.frontmatter.get("route") or ""): s for s in docs}
        for locale, docs in screens_by_locale.items()
    }

    for route, page_path in sorted(facts.pages.items()):
        for locale in LOCALES:
            if route not in routes_by_locale[locale]:
                findings.err(
                    f"{name}: page {page_path.relative_to(REPO_ROOT)} "
                    f"(route {route}) has no screen file under "
                    f"docs/user-manual/{locale}/{name}/screens/ "
                    f"(frontmatter route: {route})."
                )

    # 5. Validate every screen MD frontmatter.
    valid_endpoints = {_normalise_endpoint(m, p) for m, p in facts.endpoints}
    for locale, docs in screens_by_locale.items():
        for screen in docs:
            fm = screen.frontmatter
            rel = screen.path.relative_to(REPO_ROOT)
            if "module" not in fm or fm["module"] != name:
                findings.err(
                    f"{rel}: frontmatter `module` must equal '{name}' "
                    f"(found {fm.get('module')!r})."
                )
            route = str(fm.get("route") or "")
            if not route:
                findings.err(f"{rel}: frontmatter `route` is required.")
            elif route not in facts.pages:
                findings.warn(
                    f"{rel}: frontmatter route {route!r} does not match any "
                    f"page under {name}/frontend/pages/ "
                    f"(known: {sorted(facts.pages.keys())})."
                )
            if not fm.get("last_verified_commit"):
                findings.warn(
                    f"{rel}: frontmatter `last_verified_commit` is empty."
                )

            for ep in fm.get("related_endpoints", []) or []:
                m = re.match(r"\s*([A-Z]+)\s+(.+)\s*$", str(ep))
                if not m:
                    findings.warn(
                        f"{rel}: malformed related_endpoint {ep!r} "
                        "(expected 'METHOD /path')."
                    )
                    continue
                method, path = m.group(1), m.group(2).strip()
                key = _normalise_endpoint(method, path)
                if key not in valid_endpoints:
                    findings.warn(
                        f"{rel}: related_endpoint {method} {path} not found "
                        f"on {name}'s router (after normalising path params)."
                    )

            for perm in fm.get("related_permissions", []) or []:
                # Accept both 'patients.read' and 'read'.
                bare = str(perm).split(".", 1)[-1]
                if bare not in facts.permissions:
                    findings.warn(
                        f"{rel}: related_permission {perm!r} not in "
                        f"{name}.get_permissions() = {facts.permissions}."
                    )


def _check_orphan_screens(modules: list[str], findings: Findings) -> None:
    """Find screen MDs whose module folder doesn't exist."""
    known = set(modules)
    for locale in LOCALES:
        loc_root = USER_MANUAL_ROOT / locale
        if not loc_root.is_dir():
            continue
        for module_dir in loc_root.iterdir():
            if not module_dir.is_dir():
                continue
            if module_dir.name in {"screens"}:
                continue  # not a module folder
            if module_dir.name not in known:
                findings.warn(
                    f"docs/user-manual/{locale}/{module_dir.name}/: "
                    f"no module called '{module_dir.name}' is loaded."
                )


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def run(strict: bool) -> int:
    findings = Findings()

    modules = list(discover_modules())
    if not modules:
        findings.err(
            "No modules discovered. Ensure DENTALPIN_DEV_MODULE_SCAN=true and "
            "the backend is installed."
        )

    facts_by_name = {m.name: _collect_facts(m) for m in modules}
    for facts in facts_by_name.values():
        _check_module(facts, findings)

    _check_orphan_screens([m.name for m in modules], findings)

    if findings.warnings:
        print("Documentation coverage warnings:", file=sys.stderr)
        for w in findings.warnings:
            print(f"  ⚠  {w}", file=sys.stderr)
    if findings.errors:
        print("Documentation coverage errors:", file=sys.stderr)
        for e in findings.errors:
            print(f"  ✗  {e}", file=sys.stderr)

    if findings.ok():
        print("docs coverage OK.")
        return 0

    if strict:
        print(
            f"\nFAILED in --strict mode "
            f"({len(findings.errors)} error(s), {len(findings.warnings)} warning(s)).",
            file=sys.stderr,
        )
        return 1

    print(
        f"\n(warning-only mode — backfill in progress, "
        f"{len(findings.errors)} error(s) treated as warnings, "
        f"{len(findings.warnings)} warning(s)).",
        file=sys.stderr,
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on any violation. Default: warning-only.",
    )
    args = parser.parse_args()
    return run(strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
