#!/usr/bin/env python3
"""Backfill scaffold docs for every module that lacks them (Fase 6 of #75).

Auto-generates the per-module documentation skeletons required by the
contract in `docs/technical/documentation-portal.md`:

- ``docs/technical/<module>/overview.md``
- ``docs/technical/<module>/permissions.md`` (when the module declares any)
- ``docs/technical/<module>/events.md`` (when the module emits or
  subscribes any events)
- ``docs/user-manual/<lang>/<module>/index.md`` (when the module ships
  a Nuxt frontend layer)
- ``docs/user-manual/<lang>/<module>/screens/<slug>.md`` for every Nuxt
  page under ``<module>/frontend/pages/`` × {en, es}

Discovery reuses the helpers from ``check_docs_coverage.py`` so every
permission, endpoint, event and page lands in the scaffold consistently.

**Idempotent** — never overwrites an existing file. Run it any number
of times: it only ever creates missing scaffolds. Bumping a doc to
production quality is the author's job.

The body of each scaffold is intentionally minimal but honest: a brief
auto-generated summary plus a `> _Scaffolded stub — replace with proper
documentation._` callout. The frontmatter contract is fully populated
so the CI coverage check stops complaining.

Usage::

    python backend/scripts/scaffold_module_docs.py
    python backend/scripts/scaffold_module_docs.py --dry-run
    python backend/scripts/scaffold_module_docs.py --modules patients,recalls
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# Reuse fact-gathering from the coverage check so we don't drift.
sys.path.insert(0, str(Path(__file__).resolve().parent))


def _bootstrap_env() -> None:
    os.environ.setdefault(
        "DATABASE_URL",
        "postgresql+asyncpg://stub:stub@localhost:5432/stub",
    )
    os.environ.setdefault("SECRET_KEY", "scaffold-stub-key-32chars-minimum-12345")
    os.environ.setdefault("ENVIRONMENT", "test")
    os.environ.setdefault("TESTING", "true")
    os.environ.setdefault("DENTALPIN_DEV_MODULE_SCAN", "true")


_bootstrap_env()

from check_docs_coverage import (  # noqa: E402
    DOCS_ROOT,
    LOCALES,
    REPO_ROOT,
    TECHNICAL_ROOT,
    USER_MANUAL_ROOT,
    ModuleFacts,
    _collect_facts,
)
from app.core.plugins.loader import discover_modules  # noqa: E402

LOCALE_LABELS = {"en": "English", "es": "Español"}
STUB_NOTE_BY_LOCALE = {
    "en": "_Scaffolded stub — replace with proper documentation when this module is next touched._",
    "es": "_Esqueleto generado automáticamente — reemplazar con documentación real cuando se toque este módulo._",
}


@dataclass
class WriteAction:
    path: Path
    contents: str

    def relpath(self) -> str:
        return str(self.path.relative_to(REPO_ROOT))


def _git_short_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
        ).strip()
    except Exception:
        return "0000000"


def _slug_from_page(rel_page: Path) -> str:
    """Convert a Nuxt page path to a screen slug.

    Examples::

        recalls/index.vue          → list
        treatment-plans/[id].vue   → detail
        treatment-plans/new.vue    → create
        settings/verifactu/queue.vue → queue
    """
    stem = rel_page.with_suffix("").name
    parent = rel_page.parent.name if rel_page.parent.parts else ""
    if stem == "index":
        return "list" if parent else "index"
    if stem == "[id]":
        return "detail"
    if stem == "new":
        return "create"
    if stem.startswith("[") and stem.endswith("]"):
        return stem
    return stem


def _format_endpoint(method: str, path: str) -> str:
    return f"{method.upper()} {path}"


def _normalise_perm(name: str, module_name: str) -> str:
    if name.startswith(f"{module_name}."):
        return name
    return f"{module_name}.{name}"


def _yaml_list(items: list[str]) -> str:
    if not items:
        return "[]"
    return "\n" + "\n".join(f"  - {item}" for item in items)


def _technical_overview(facts: ModuleFacts, head: str, locale: str = "en") -> str:
    perms = ", ".join(f"`{p}`" for p in facts.permissions) or "_(none)_"
    events_emit = ", ".join(f"`{e}`" for e in facts.events_emitted) or "_(none)_"
    events_sub = ", ".join(f"`{e}`" for e in facts.events_consumed) or "_(none)_"
    endpoints = (
        "\n".join(f"- `{_format_endpoint(m, p)}`" for m, p in sorted(facts.endpoints))
        or "_No HTTP endpoints._"
    )
    pages = (
        "\n".join(f"- `{p.relative_to(REPO_ROOT)}` → `{r}`" for r, p in sorted(facts.pages.items()))
        or "_This module ships no Nuxt pages._"
    )

    permissions_link = (
        "\nSee [`./permissions.md`](./permissions.md) for the full role mapping."
        if facts.permissions
        else ""
    )
    events_section = (
        f"""## Events

- **Emits:** {events_emit}
- **Subscribes:** {events_sub}

See [`./events.md`](./events.md) for the per-event detail.
"""
        if (facts.events_emitted or facts.events_consumed)
        else ""
    )

    return f"""---
module: {facts.name}
last_verified_commit: {head}
---

# {facts.name.replace('_', ' ').title()} — technical overview

> {STUB_NOTE_BY_LOCALE['en']}

Auto-discovered facts about the `{facts.name}` module. See the module's
own notes at `backend/app/modules/{facts.name}/CLAUDE.md` for context
the scaffold could not infer.

## API surface

{endpoints}

## Frontend

{pages}

## Permissions

{perms}{permissions_link}

{events_section}
## See also

- Module CLAUDE notes: `backend/app/modules/{facts.name}/CLAUDE.md`
- [Documentation portal contract](../../technical/documentation-portal.md)
"""


def _technical_permissions(facts: ModuleFacts, head: str) -> str:
    if not facts.permissions:
        return ""
    rows: list[str] = []
    for perm in facts.permissions:
        full = _normalise_perm(perm, facts.name)
        # Best-effort: list every endpoint that mentions the bare perm
        # name in its decorator path. Authors refine later.
        rows.append(f"| `{full}` | _Describe what this allows._ | _List the endpoints._ |")
    return f"""---
module: {facts.name}
last_verified_commit: {head}
---

# {facts.name.replace('_', ' ').title()} — permissions

> {STUB_NOTE_BY_LOCALE['en']}

Returned by `{facts.name.title().replace('_', '')}Module.get_permissions()`
(relative names; the registry namespaces them as `{facts.name}.<name>`).

| Permission | Allows | Required by |
|------------|--------|-------------|
{chr(10).join(rows)}

## Role assignment

See `backend/app/core/auth/permissions.py` for the canonical role table.

## Adding a new permission

1. Add the relative name to `get_permissions()` in
   `backend/app/modules/{facts.name}/__init__.py` (or `module.py`).
2. Add the namespaced form to the relevant role(s) in
   `backend/app/core/auth/permissions.py`.
3. Add a row to the table above.
4. Annotate the endpoint(s) with `Depends(require_permission(...))`.
5. Update `frontend/app/config/permissions.ts` if it gates UI.
"""


def _technical_events(facts: ModuleFacts, head: str) -> str:
    if not facts.events_emitted and not facts.events_consumed:
        return ""

    emitted_rows = (
        "\n".join(
            f"| `{e}` | _When does this fire?_ | _Payload keys._ |"
            for e in facts.events_emitted
        )
        or "_This module does not publish any events._"
    )
    consumed_rows = (
        "\n".join(
            f"| `{e}` | _Handler module path._ | _What it does in response._ |"
            for e in facts.events_consumed
        )
        or "_This module does not subscribe to any events._"
    )

    emitted_block = (
        "| Event | When | Payload |\n|-------|------|---------|\n" + emitted_rows
        if facts.events_emitted
        else emitted_rows
    )
    consumed_block = (
        "| Event | Handler | Effect |\n|-------|---------|--------|\n" + consumed_rows
        if facts.events_consumed
        else consumed_rows
    )

    return f"""---
module: {facts.name}
last_verified_commit: {head}
---

# {facts.name.replace('_', ' ').title()} — events

> {STUB_NOTE_BY_LOCALE['en']}

Per-module slice of [`docs/events-catalog.md`](../../events-catalog.md)
(auto-generated). Update both files when adding or removing events.

## Published

{emitted_block}

## Subscribed

{consumed_block}

## Adding a new event

1. Add the constant to `backend/app/core/events/types.py` (`EventType`).
2. Publish from a service method, after the DB commit succeeds.
3. Add the row to the table(s) above.
4. Run `python backend/scripts/generate_catalogs.py` to refresh the
   global catalog.
"""


def _user_manual_index(facts: ModuleFacts, head: str, locale: str) -> str:
    title = facts.name.replace("_", " ").title()
    if locale == "es":
        return f"""---
module: {facts.name}
last_verified_commit: {head}
---

# {title}

> {STUB_NOTE_BY_LOCALE['es']}

Página de aterrizaje del módulo `{facts.name}` en el manual de usuario.

## Pantallas

{('Este módulo no aporta páginas Nuxt propias.' if not facts.pages else chr(10).join(f'- `{r}` — _Pendiente de documentar._' for r in sorted(facts.pages)))}

## Permisos

{('_(sin permisos)_' if not facts.permissions else chr(10).join(f'- `{_normalise_perm(p, facts.name)}`' for p in facts.permissions))}

## Recursos técnicos

- [Resumen técnico](../../../technical/{facts.name}/overview.md)
- [Permisos](../../../technical/{facts.name}/permissions.md)
- [Eventos](../../../technical/{facts.name}/events.md)
"""

    return f"""---
module: {facts.name}
last_verified_commit: {head}
---

# {title}

> {STUB_NOTE_BY_LOCALE['en']}

Landing page for the `{facts.name}` module in the end-user manual.

## Screens

{('This module ships no Nuxt pages of its own.' if not facts.pages else chr(10).join(f'- `{r}` — _Documentation pending._' for r in sorted(facts.pages)))}

## Permissions

{('_(none)_' if not facts.permissions else chr(10).join(f'- `{_normalise_perm(p, facts.name)}`' for p in facts.permissions))}

## Technical references

- [Technical overview](../../../technical/{facts.name}/overview.md)
- [Permissions](../../../technical/{facts.name}/permissions.md)
- [Events](../../../technical/{facts.name}/events.md)
"""


def _screen_doc(
    facts: ModuleFacts,
    route: str,
    page_path: Path,
    head: str,
    locale: str,
) -> str:
    related_endpoints = sorted(
        f"{m} {p}" for m, p in facts.endpoints
    )
    related_permissions = [
        _normalise_perm(p, facts.name) for p in facts.permissions
    ]
    rel_page = page_path.relative_to(REPO_ROOT).as_posix()

    if locale == "es":
        body_intro = (
            f"_Pantalla `{route}` del módulo `{facts.name}`._\n\n"
            "## Permisos\n\n"
            + ("\n".join(f"- `{p}`" for p in related_permissions) or "_(sin permisos específicos)_")
            + "\n\n"
            "## Para qué sirve\n\n_Pendiente de documentar._\n"
        )
    else:
        body_intro = (
            f"_Screen `{route}` of the `{facts.name}` module._\n\n"
            "## Permissions\n\n"
            + ("\n".join(f"- `{p}`" for p in related_permissions) or "_(no specific permissions)_")
            + "\n\n"
            "## What this screen does\n\n_Documentation pending._\n"
        )

    return f"""---
module: {facts.name}
screen: {_semantic_screen_label(route)}
route: {route}
related_endpoints:{_yaml_list(related_endpoints)}
related_permissions:{_yaml_list(related_permissions)}
related_paths:
  - {rel_page}
last_verified_commit: {head}
---

# {route}

> {STUB_NOTE_BY_LOCALE[locale]}

{body_intro}
"""


def _semantic_screen_label(route: str) -> str:
    """Best-guess `screen:` field — 'list' / 'detail' / 'create' / 'edit' /
    or the last segment for nested routes. Informational only; the
    filename slug is derived from the full route to stay unique."""
    trimmed = route.strip("/")
    if not trimmed:
        return "home"
    parts = trimmed.split("/")
    last = parts[-1]
    if last == "[id]" or (last.startswith("[") and last.endswith("]")):
        return "detail"
    if last == "new":
        return "create"
    if last == "edit":
        return "edit"
    if len(parts) == 1:
        return "list"
    return last.replace("[", "").replace("]", "").replace("...", "")


def _filename_slug_from_route(route: str) -> str:
    """Filename for the screen MD — matches the help-fragment slug rule
    in `docs/portal/.vitepress/help.ts` so the source MD lines up with
    the rendered fragment URL.

    `/recalls`              → `recalls`
    `/treatment-plans/[id]` → `treatment-plans_[id]`
    `/invoices/[id]/edit`   → `invoices_[id]_edit`
    `/`                     → `index`
    """
    trimmed = route.strip("/")
    if not trimmed:
        return "index"
    return trimmed.replace("/", "_")


def _gather_actions(facts: ModuleFacts, head: str) -> list[WriteAction]:
    actions: list[WriteAction] = []
    tech_dir = TECHNICAL_ROOT / facts.name

    overview = tech_dir / "overview.md"
    if not overview.is_file():
        actions.append(WriteAction(overview, _technical_overview(facts, head)))

    if facts.permissions:
        perms = tech_dir / "permissions.md"
        if not perms.is_file():
            actions.append(WriteAction(perms, _technical_permissions(facts, head)))

    if facts.events_emitted or facts.events_consumed:
        events = tech_dir / "events.md"
        if not events.is_file():
            actions.append(WriteAction(events, _technical_events(facts, head)))

    if facts.has_frontend:
        for locale in LOCALES:
            module_dir = USER_MANUAL_ROOT / locale / facts.name
            index = module_dir / "index.md"
            if not index.is_file():
                actions.append(
                    WriteAction(index, _user_manual_index(facts, head, locale))
                )

    # Pre-scan existing screen MDs per locale, key by frontmatter route
    # so we don't overwrite hand-authored docs that use semantic filenames
    # (e.g. `list.md`, `detail.md`) when the scaffold would pick a
    # route-based filename for the same route.
    documented_routes_by_locale: dict[str, set[str]] = {loc: set() for loc in LOCALES}
    for locale in LOCALES:
        screens_dir = USER_MANUAL_ROOT / locale / facts.name / "screens"
        if not screens_dir.is_dir():
            continue
        for md in screens_dir.glob("*.md"):
            text = md.read_text(encoding="utf-8", errors="replace")
            if not text.startswith("---"):
                continue
            end = text.find("\n---", 3)
            if end == -1:
                continue
            for line in text[3:end].splitlines():
                if line.startswith("route:"):
                    documented_routes_by_locale[locale].add(
                        line.split(":", 1)[1].strip().strip("\"'")
                    )
                    break

    for route, page_path in sorted(facts.pages.items()):
        slug = _filename_slug_from_route(route)
        for locale in LOCALES:
            if route in documented_routes_by_locale[locale]:
                continue
            screen_path = (
                USER_MANUAL_ROOT / locale / facts.name / "screens" / f"{slug}.md"
            )
            if screen_path.is_file():
                continue
            actions.append(
                WriteAction(
                    screen_path,
                    _screen_doc(facts, route, page_path, head, locale),
                )
            )

    return actions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be written but don't touch the filesystem.",
    )
    parser.add_argument(
        "--modules",
        type=str,
        default="",
        help="Comma-separated list of module names. Default: all modules.",
    )
    args = parser.parse_args()

    head = _git_short_head()
    requested = {m.strip() for m in args.modules.split(",") if m.strip()}

    modules = list(discover_modules())
    facts_by_name = {m.name: _collect_facts(m) for m in modules}

    actions: list[WriteAction] = []
    for name, facts in sorted(facts_by_name.items()):
        if requested and name not in requested:
            continue
        actions.extend(_gather_actions(facts, head))

    if not actions:
        print("All scaffolds already in place. Nothing to do.")
        return 0

    print(f"{'Would create' if args.dry_run else 'Creating'} {len(actions)} file(s):\n")
    for action in actions:
        print(f"  + {action.relpath()}")
        if not args.dry_run:
            action.path.parent.mkdir(parents=True, exist_ok=True)
            action.path.write_text(action.contents, encoding="utf-8")

    if args.dry_run:
        print("\n(dry-run — pass without --dry-run to write the files)")
    else:
        print(
            f"\nWrote {len(actions)} file(s). Review them, replace stub bodies "
            "with real prose, then run `python backend/scripts/check_docs_coverage.py`."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
