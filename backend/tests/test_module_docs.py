"""Per-module documentation presence guard.

Every module discovered by the loader MUST ship two AI-agent-facing
docs alongside its code:

- ``backend/app/modules/<name>/CLAUDE.md`` — purpose, public API,
  events, permissions, gotchas. Template:
  ``docs/checklists/module-claude-template.md``.
- ``backend/app/modules/<name>/CHANGELOG.md`` — per-module Keep-a-
  Changelog so history is local to the module without `git log`
  archaeology.

If you are adding a new module and this test is failing, you forgot
the docs. Copy the template, fill it, commit. The PR template at
``.github/PULL_REQUEST_TEMPLATE.md`` lists every action a new module
requires.

Both files must be non-trivial (≥ ~10 useful lines). Empty stubs
defeat the purpose; CI rejects them.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.plugins.loader import discover_modules

MODULES_ROOT = Path(__file__).resolve().parents[1] / "app" / "modules"

REQUIRED_DOCS = ("CLAUDE.md", "CHANGELOG.md")

# Minimum non-blank lines per doc. Tuned so that a CHANGELOG with just
# `# Title`, `## Unreleased`, one bullet, `## 0.1.0` and a couple of
# bullets passes; an empty stub doesn't. CLAUDE.md is held to a higher
# bar via its dedicated content threshold.
MIN_NON_BLANK_LINES = {"CLAUDE.md": 12, "CHANGELOG.md": 5}


@pytest.fixture(scope="module")
def discovered_module_names() -> list[str]:
    names = sorted(m.name for m in discover_modules())
    assert names, "module discovery returned no modules"
    return names


@pytest.mark.parametrize("doc_name", REQUIRED_DOCS)
def test_every_module_has_doc(discovered_module_names: list[str], doc_name: str) -> None:
    missing: list[str] = []
    too_short: list[tuple[str, int]] = []

    threshold = MIN_NON_BLANK_LINES[doc_name]

    for module_name in discovered_module_names:
        path = MODULES_ROOT / module_name / doc_name
        if not path.exists():
            missing.append(module_name)
            continue
        non_blank = sum(1 for line in path.read_text().splitlines() if line.strip())
        if non_blank < threshold:
            too_short.append((module_name, non_blank))

    assert not missing, (
        f"Modules missing {doc_name}: {missing}. "
        f"Copy docs/checklists/module-claude-template.md and fill it in."
    )
    assert not too_short, (
        f"Modules with sparse {doc_name} (<{threshold} non-blank lines): "
        f"{too_short}. Flesh out the doc — empty stubs defeat the purpose."
    )
