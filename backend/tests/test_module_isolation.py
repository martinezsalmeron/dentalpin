"""Module isolation guard.

Each module under ``app.modules`` must only import other modules that
are listed in its own ``manifest.depends``. Reads via ORM, services or
plain ``app.modules.X`` paths all count as "imports" — the only legal
cross-module communication outside of ``depends`` is the event bus.

This test is a CI guard: when a refactor introduces a stealth
cross-module dependency, the failure here is the early warning.

The check is intentionally minimal:

- Walks every Python file inside ``backend/app/modules/<module>/``.
- Greps for ``from app.modules.<other>`` and ``import app.modules.<other>``.
- Allows the module to import itself, ``app.core.*``, ``app.database``,
  and any module name listed in its manifest's ``depends``.
- TYPE_CHECKING blocks are skipped (typing-only imports do not create
  runtime coupling).

If you need a new cross-module dependency, declare it in the offending
module's ``manifest.depends`` (and create the cross-module FK / event
contract that the dependency justifies).
"""

from __future__ import annotations

import ast
import importlib
import re
from pathlib import Path

import app.modules as _modules_pkg  # noqa: E402  (must come before path constants)

# Locate the modules directory regardless of whether tests run from the
# repo root (host) or from /app (container).
MODULES_ROOT = Path(_modules_pkg.__file__).resolve().parent
REPO_ROOT = MODULES_ROOT.parents[2]

CROSS_IMPORT_RE = re.compile(
    r"^\s*(?:from\s+app\.modules\.([a-z_]+)|import\s+app\.modules\.([a-z_]+))",
    re.MULTILINE,
)


def _load_manifest_depends(module_name: str) -> set[str]:
    pkg = importlib.import_module(f"app.modules.{module_name}")
    # Each module exposes a class subclassing BaseModule with a ``manifest``
    # dict attribute. Find it dynamically.
    for attr in vars(pkg).values():
        if (
            isinstance(attr, type)
            and getattr(attr, "manifest", None)
            and isinstance(attr.manifest, dict)
            and attr.manifest.get("name") == module_name
        ):
            return set(attr.manifest.get("depends", []))
    raise AssertionError(f"Could not locate manifest for module {module_name}")


def _strip_type_checking_blocks(source: str) -> str:
    """Remove ``if TYPE_CHECKING:`` blocks so typing-only imports are not
    flagged.

    The check is line-based and conservative — anything indented under an
    ``if TYPE_CHECKING:`` line is dropped until the indent returns to the
    block's level. Good enough for our codebase style; not a full Python
    parser.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return source

    lines = source.splitlines(keepends=True)
    drop_ranges: list[tuple[int, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            test = node.test
            is_type_checking = (isinstance(test, ast.Name) and test.id == "TYPE_CHECKING") or (
                isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING"
            )
            if is_type_checking:
                end = node.end_lineno or node.lineno
                drop_ranges.append((node.lineno - 1, end))

    if not drop_ranges:
        return source

    for start, end in sorted(drop_ranges, reverse=True):
        del lines[start:end]
    return "".join(lines)


def _list_modules() -> list[str]:
    return sorted(
        p.name for p in MODULES_ROOT.iterdir() if p.is_dir() and (p / "__init__.py").exists()
    )


# Pre-existing cross-module imports that are tracked tech debt. Each
# tuple is ``(module, file_relative_to_module, target_module)``. The
# guard fails if the actual set of violations diverges from this set —
# any new violation surfaces immediately, and removing a violation also
# fails until the allowlist is updated (forcing the cleanup to be
# explicit). The goal is to drain this set over time, not grow it.
KNOWN_VIOLATIONS: set[tuple[str, str, str]] = {
    ("agenda", "service.py", "odontogram"),
    ("agenda", "service.py", "treatment_plan"),
    ("agenda", "kanban_service.py", "schedules"),
    ("billing", "router.py", "reports"),
    ("catalog", "service.py", "billing"),
    ("catalog", "service.py", "budget"),
    ("clinical_notes", "service.py", "agenda"),
    ("notifications", "handlers.py", "catalog"),
    ("notifications", "router.py", "catalog"),
    ("patient_timeline", "seed.py", "agenda"),
    ("patient_timeline", "seed.py", "billing"),
    ("patient_timeline", "seed.py", "budget"),
    ("patient_timeline", "seed.py", "odontogram"),
    ("patient_timeline", "seed.py", "treatment_plan"),
    ("patients", "service.py", "agenda"),
}


def _scan_module_violations(module_name: str) -> set[tuple[str, str, str]]:
    depends = _load_manifest_depends(module_name)
    allowed = depends | {module_name}
    module_root = MODULES_ROOT / module_name
    found: set[tuple[str, str, str]] = set()
    for py_path in module_root.rglob("*.py"):
        if "/migrations/" in str(py_path):
            continue
        text = py_path.read_text(encoding="utf-8")
        text = _strip_type_checking_blocks(text)
        for match in CROSS_IMPORT_RE.finditer(text):
            other = match.group(1) or match.group(2)
            if other in allowed:
                continue
            relative = str(py_path.relative_to(module_root))
            found.add((module_name, relative, other))
    return found


def test_no_new_cross_module_imports() -> None:
    """The set of cross-module imports outside ``manifest.depends`` must
    match the known-tech-debt allowlist exactly."""
    actual: set[tuple[str, str, str]] = set()
    for module_name in _list_modules():
        actual |= _scan_module_violations(module_name)

    new_violations = actual - KNOWN_VIOLATIONS
    resolved_violations = KNOWN_VIOLATIONS - actual

    messages: list[str] = []
    if new_violations:
        messages.append(
            "New cross-module imports detected (must be in manifest.depends or removed):"
        )
        for module_name, path, target in sorted(new_violations):
            messages.append(f"  - {module_name}/{path} imports app.modules.{target}")
    if resolved_violations:
        messages.append("Pre-existing violations cleared. Remove from KNOWN_VIOLATIONS:")
        for module_name, path, target in sorted(resolved_violations):
            messages.append(f"  - {module_name}/{path} imports app.modules.{target}")

    assert not messages, "\n".join(messages)
