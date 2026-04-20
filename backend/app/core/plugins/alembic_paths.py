"""Helpers shared between :mod:`alembic.env` and tests.

Kept outside the ``alembic/env.py`` script because that file is executed
by Alembic at import time and is awkward to import from tests.
"""

from __future__ import annotations

from pathlib import Path


def discover_version_locations(
    main_linear: Path,
    modules_root: Path,
) -> list[str]:
    """Return the main linear path + every existing per-module branch.

    A module is treated as contributing a branch when it has a directory
    ``<modules_root>/<name>/migrations/versions/``. Directories whose
    name starts with ``_`` are skipped so tests can stash scratch data
    under ``<modules_root>/__scratch__/`` without polluting real
    discovery.

    This is intentionally filesystem-only — the function runs during
    Alembic bootstrap when ``core_module`` may not exist yet, and in
    offline (``--sql``) mode where no database connection is available.
    """
    locations: list[str] = [str(main_linear)]

    if modules_root.is_dir():
        for module_dir in sorted(modules_root.iterdir()):
            if not module_dir.is_dir() or module_dir.name.startswith("_"):
                continue
            branch = module_dir / "migrations" / "versions"
            if branch.is_dir():
                locations.append(str(branch))

    return locations
