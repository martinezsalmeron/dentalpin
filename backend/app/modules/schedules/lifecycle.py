"""Install / uninstall / upgrade hooks.

The 24/7 default seed runs in the Alembic migration itself (data
migration step inside ``sch_0001_initial.py``) so the behavior is the
same whether the module is discovered on a fresh database or installed
later via ``dentalpin modules install schedules``.
"""

from __future__ import annotations

import logging

from app.core.plugins import ModuleContext

logger = logging.getLogger(__name__)


async def install(ctx: ModuleContext) -> None:
    ctx.logger.info("schedules module installed")


async def uninstall(ctx: ModuleContext) -> None:
    ctx.logger.info("schedules module uninstalling")


async def post_upgrade(ctx: ModuleContext, from_version: str) -> None:
    ctx.logger.info("schedules upgraded from %s", from_version)
