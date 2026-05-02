#!/usr/bin/env python3
"""Enforce the `/docs` folder taxonomy (issue #67).

CI fails if any of the following is violated:

1. A markdown file lives at `docs/` root that is NOT in the root allowlist.
2. A folder exists directly under `docs/` that is NOT in the folder allowlist.
3. An image asset (`.png`, `.jpg`, `.jpeg`, `.gif`, `.svg`, `.webp`) lives
   anywhere under `docs/` outside `docs/screenshots/` or `docs/diagrams/`.

The taxonomy + routing rule is documented in:
- root `CLAUDE.md` ("Documentation policy")
- `docs/README.md` (decision tree + folder descriptions)

Run::

    python scripts/check_docs_layout.py            # exit 1 on violations
    python scripts/check_docs_layout.py --list     # print the allowlists

Mirrors the read-only posture of ``backend/scripts/generate_catalogs.py``.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DOCS = REPO / "docs"

ROOT_FILES_ALLOWED: frozenset[str] = frozenset(
    {
        "README.md",
        "glossary.md",
        "events-catalog.md",
        "modules-catalog.md",
    }
)

FOLDERS_ALLOWED: frozenset[str] = frozenset(
    {
        "user-manual",
        "features",
        "technical",
        "modules",
        "adr",
        "checklists",
        "diagrams",
        "screenshots",
        "workflows",
        # VitePress portal that renders the rest of /docs (ADR 0009).
        # It owns the build pipeline only — no documentation content lives
        # here. See docs/portal/README.md.
        "portal",
    }
)

IMAGE_EXTS: frozenset[str] = frozenset(
    {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}
)
IMAGE_FOLDERS: frozenset[str] = frozenset({"screenshots", "diagrams"})


def check() -> list[str]:
    violations: list[str] = []

    if not DOCS.is_dir():
        return [f"{DOCS} is not a directory — nothing to check."]

    for entry in sorted(DOCS.iterdir()):
        if entry.name.startswith("."):
            continue  # ignore .DS_Store etc — git ignores them anyway
        if entry.is_file():
            if entry.suffix == ".md" and entry.name not in ROOT_FILES_ALLOWED:
                violations.append(
                    f"docs/{entry.name}: markdown not allowed at docs/ root. "
                    "Move to a topic folder (see docs/README.md)."
                )
            elif entry.suffix in IMAGE_EXTS:
                violations.append(
                    f"docs/{entry.name}: image at docs/ root. "
                    "Move to docs/screenshots/ or docs/diagrams/."
                )
        elif entry.is_dir() and entry.name not in FOLDERS_ALLOWED:
            violations.append(
                f"docs/{entry.name}/: folder not in the taxonomy. "
                f"Allowed folders: {', '.join(sorted(FOLDERS_ALLOWED))}."
            )

    # Image-placement check across the whole docs/ tree.
    for path in DOCS.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in IMAGE_EXTS:
            continue
        rel = path.relative_to(DOCS)
        top = rel.parts[0] if rel.parts else ""
        if top not in IMAGE_FOLDERS:
            violations.append(
                f"docs/{rel.as_posix()}: image outside docs/screenshots/ "
                "or docs/diagrams/."
            )

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--list",
        action="store_true",
        help="Print the allowlists and exit 0.",
    )
    args = parser.parse_args()

    if args.list:
        print("Root files allowed:")
        for name in sorted(ROOT_FILES_ALLOWED):
            print(f"  {name}")
        print("\nTopic folders allowed:")
        for name in sorted(FOLDERS_ALLOWED):
            print(f"  {name}/")
        print(f"\nImage extensions: {', '.join(sorted(IMAGE_EXTS))}")
        print(f"Image folders only: {', '.join(sorted(IMAGE_FOLDERS))}")
        return 0

    violations = check()
    if violations:
        print("docs layout violations:", file=sys.stderr)
        for v in violations:
            print(f"  - {v}", file=sys.stderr)
        print(
            "\nSee docs/README.md and the 'Documentation policy' section "
            "of root CLAUDE.md for the taxonomy.",
            file=sys.stderr,
        )
        return 1

    print("docs layout OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
