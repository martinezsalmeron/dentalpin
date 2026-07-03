"""Cross-module foreign-key guard (audit S4, #94).

CLAUDE.md's modular contract states: "Cross-module FKs are allowed **only**
when the target is in the module's ``manifest.depends``. CI rejects
migrations otherwise." That CI check did not exist — the import guard in
``test_module_isolation.py`` only looks at Python imports and explicitly
skips ``migrations/``, so a migration adding a cross-module FK (or a model
column pointing at another module's table) was invisible.

This test closes that gap by introspecting the SQLAlchemy models: for
every ``ForeignKey`` whose target table is owned by another module, that
module must be in the source module's ``depends`` — unless the target is
a core table (``clinics``, ``users``, …), which is always allowed.

Ratchet, like the import guard: the actual set of cross-module FKs must
equal ``KNOWN_FK_VIOLATIONS`` exactly. A new violation fails immediately;
clearing one also fails until the allowlist is updated, forcing the
cleanup to be explicit. Drain this set over time, never grow it.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import app.modules as _modules_pkg
from app.database import Base

MODULES_ROOT = Path(_modules_pkg.__file__).resolve().parent


# Pre-existing cross-module FKs that are tracked tech debt.
# ``(source_module, table, column, target_table, target_module)``.
# agenda→treatment_plan mirrors the import already tracked in
# test_module_isolation.KNOWN_VIOLATIONS (the appointment↔plan-item link).
KNOWN_FK_VIOLATIONS: set[tuple[str, str, str, str, str]] = {
    (
        "agenda",
        "appointment_treatments",
        "planned_treatment_item_id",
        "planned_treatment_items",
        "treatment_plan",
    ),
}


def _list_modules() -> list[str]:
    return sorted(
        p.name for p in MODULES_ROOT.iterdir() if p.is_dir() and (p / "__init__.py").exists()
    )


def _import_all_models() -> None:
    """Ensure every module's models are registered on ``Base`` before we
    walk the mapper registry."""
    for name in _list_modules():
        importlib.import_module(f"app.modules.{name}")
        try:
            importlib.import_module(f"app.modules.{name}.models")
        except ModuleNotFoundError:
            continue  # module owns no tables (e.g. accounting_export)


def _manifest_depends(module_name: str) -> set[str]:
    pkg = importlib.import_module(f"app.modules.{module_name}")
    for attr in vars(pkg).values():
        if (
            isinstance(attr, type)
            and getattr(attr, "manifest", None)
            and isinstance(attr.manifest, dict)
            and attr.manifest.get("name") == module_name
        ):
            return set(attr.manifest.get("depends", []))
    raise AssertionError(f"Could not locate manifest for module {module_name}")


def _table_owner_map() -> dict[str, str]:
    """``tablename -> owning module`` for module-defined tables. Tables not
    in this map are core (``app.core.*``) and always FK-legal."""
    owner: dict[str, str] = {}
    for mapper in Base.registry.mappers:
        module = mapper.class_.__module__
        if not module.startswith("app.modules."):
            continue
        tablename = getattr(mapper.class_, "__tablename__", None)
        if tablename:
            owner[tablename] = module.split(".")[2]
    return owner


def _scan_cross_module_fks() -> set[tuple[str, str, str, str, str]]:
    owner = _table_owner_map()
    depends_cache: dict[str, set[str]] = {}
    found: set[tuple[str, str, str, str, str]] = set()

    for mapper in Base.registry.mappers:
        module = mapper.class_.__module__
        if not module.startswith("app.modules."):
            continue
        source = module.split(".")[2]
        depends = depends_cache.setdefault(source, _manifest_depends(source))
        for column in mapper.class_.__table__.columns:
            for fk in column.foreign_keys:
                target_table = fk.column.table.name
                target_module = owner.get(target_table)
                if target_module and target_module != source and target_module not in depends:
                    found.add(
                        (
                            source,
                            mapper.class_.__tablename__,
                            column.name,
                            target_table,
                            target_module,
                        )
                    )
    return found


def test_no_undeclared_cross_module_fks() -> None:
    _import_all_models()
    actual = _scan_cross_module_fks()

    new = actual - KNOWN_FK_VIOLATIONS
    resolved = KNOWN_FK_VIOLATIONS - actual

    messages: list[str] = []
    if new:
        messages.append(
            "New cross-module FKs detected — declare the target in the source "
            "module's manifest.depends, or remove the FK:"
        )
        for src, table, col, tgt_table, tgt_mod in sorted(new):
            messages.append(
                f"  - {src}.{table}.{col} -> {tgt_table} (owned by {tgt_mod}); "
                f"'{tgt_mod}' not in {src}.depends"
            )
    if resolved:
        messages.append("Cross-module FK cleared. Remove from KNOWN_FK_VIOLATIONS:")
        for src, table, col, tgt_table, tgt_mod in sorted(resolved):
            messages.append(f"  - {src}.{table}.{col} -> {tgt_table} ({tgt_mod})")

    assert not messages, "\n".join(messages)
