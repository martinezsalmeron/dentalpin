"""Install / uninstall hooks.

Schema is created and dropped by Alembic; this hook only logs the
transition. Staging files on disk are removed on uninstall so
removing the module doesn't leave gigabytes of DPMF binaries behind.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from app.config import settings
from app.core.plugins import ModuleContext

logger = logging.getLogger(__name__)


def _staging_root() -> Path:
    """Filesystem root where uploaded DPMF files are staged."""
    base = getattr(settings, "MIGRATION_IMPORT_STAGING_DIR", None)
    if base:
        return Path(base)
    return Path("/var/lib/dentalpin/migration-import")


async def install(ctx: ModuleContext) -> None:
    ctx.logger.info("migration_import installed")
    _staging_root().mkdir(parents=True, exist_ok=True)


async def uninstall(ctx: ModuleContext) -> None:
    ctx.logger.info("migration_import uninstalling — wiping DPMF staging")
    root = _staging_root()
    if root.exists():
        shutil.rmtree(root, ignore_errors=True)
