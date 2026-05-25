"""Install / uninstall / upgrade hooks for the periodontogram module."""

from __future__ import annotations

import logging

from app.core.plugins import ModuleContext

logger = logging.getLogger(__name__)


async def install(ctx: ModuleContext) -> None:
    ctx.logger.info("periodontogram module installed")


async def uninstall(ctx: ModuleContext) -> None:
    ctx.logger.info("periodontogram module uninstalling")


async def post_upgrade(ctx: ModuleContext, from_version: str) -> None:
    ctx.logger.info("periodontogram upgraded from %s", from_version)
