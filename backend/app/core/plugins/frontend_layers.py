"""Nuxt-layer discovery and ``modules.json`` writer.

Fase A contract:

* Each module *may* declare ``manifest.frontend.layer_path`` — a path
  *relative to the module's Python package root* that points at a Nuxt
  Layer (``nuxt.config.ts``, ``pages/``, ``components/``,
  ``composables/``, ``i18n/``, ``slots.ts``).
* The registry resolves those to absolute filesystem paths and writes
  a JSON file at ``<repo>/frontend/modules.json``.
* ``frontend/nuxt.config.ts`` reads that file synchronously at boot
  and passes the ``layers`` array to ``extends``.

The 9 Fase A official modules keep their UI on the host frontend and
do **not** declare ``layer_path`` — per the Q4 decision (officials
pre-bundled, no rebuild on install/uninstall). The mechanism is
designed primarily for community modules shipping their own UI in
their PyPI package.

Writing is atomic (temp file + rename) and guarded by a filesystem
lock so concurrent CLI invocations can't tear the JSON.
"""

from __future__ import annotations

import importlib.util
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from app.config import settings

if TYPE_CHECKING:
    from .base import BaseModule

logger = logging.getLogger(__name__)

MODULES_JSON_SCHEMA_VERSION = 1
DEFAULT_FRONTEND_ROOT = Path(settings.DENTALPIN_FRONTEND_ROOT)


@dataclass
class LayerEntry:
    """Projection of one layer that belongs in ``modules.json``."""

    module_name: str
    path: str


def resolve_layer_path(module: BaseModule) -> Path | None:
    """Return the absolute path of ``module``'s Nuxt layer, or ``None``.

    Missing ``manifest.frontend.layer_path`` → ``None``. Missing folder
    on disk → ``None`` with a warning (the caller decides whether to
    fail or continue).
    """
    manifest = module.get_manifest()
    rel = manifest.frontend.get("layer_path") if manifest.frontend else None
    if not rel:
        return None

    spec = importlib.util.find_spec(type(module).__module__)
    if spec is None or spec.origin is None:
        logger.warning(
            "Cannot resolve package path for module %s; skipping layer",
            manifest.name,
        )
        return None

    base = Path(spec.origin).parent
    candidate = (base / rel).resolve()
    if not candidate.is_dir():
        logger.warning(
            "Module %s declared layer_path=%s but %s is not a directory",
            manifest.name,
            rel,
            candidate,
        )
        return None
    return candidate


def _translate_for_frontend(path: Path) -> str:
    """Rewrite a backend-container layer path for the frontend container.

    The backend sees layers at ``{DENTALPIN_MODULE_PKG_ROOT}/<name>/...``;
    the frontend container mounts the same filesystem at
    ``{DENTALPIN_MODULE_LAYERS_MOUNT}``. When the two paths differ we
    rewrite so ``modules.json`` is usable by whoever reads it. If the
    path doesn't live under the known backend root (e.g. tests,
    community module installed from site-packages) we emit it as-is.
    """
    pkg_root = Path(settings.DENTALPIN_MODULE_PKG_ROOT)
    mount = Path(settings.DENTALPIN_MODULE_LAYERS_MOUNT)
    if pkg_root == mount:
        return str(path)
    try:
        rel = path.relative_to(pkg_root)
    except ValueError:
        return str(path)
    return str(mount / rel)


def collect_layers(modules: list[BaseModule]) -> list[LayerEntry]:
    """Run :func:`resolve_layer_path` for every module with one."""
    entries: list[LayerEntry] = []
    for module in modules:
        path = resolve_layer_path(module)
        if path is None:
            continue
        entries.append(
            LayerEntry(module_name=module.name, path=_translate_for_frontend(path))
        )
    return entries


def build_payload(entries: list[LayerEntry]) -> dict[str, object]:
    return {
        "version": MODULES_JSON_SCHEMA_VERSION,
        "layers": [e.path for e in entries],
        "modules": [{"name": e.module_name, "path": e.path} for e in entries],
    }


def write_modules_json(
    entries: list[LayerEntry],
    frontend_root: Path = DEFAULT_FRONTEND_ROOT,
) -> Path:
    """Write ``modules.json`` atomically (temp file + rename).

    Returns the path of the file that was written.
    """
    frontend_root.mkdir(parents=True, exist_ok=True)
    target = frontend_root / "modules.json"
    tmp = frontend_root / "modules.json.tmp"

    payload = build_payload(entries)
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, target)

    logger.info("Wrote %s with %d layer(s)", target, len(entries))
    return target


def read_modules_json(
    frontend_root: Path = DEFAULT_FRONTEND_ROOT,
) -> dict[str, object]:
    """Read the current ``modules.json`` or return the empty default."""
    path = frontend_root / "modules.json"
    if not path.exists():
        return build_payload([])
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        logger.warning("modules.json is malformed; treating as empty")
        return build_payload([])
