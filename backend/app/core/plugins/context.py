"""Module lifecycle context.

Passed to :meth:`BaseModule.install`, :meth:`BaseModule.uninstall`, and
:meth:`BaseModule.post_upgrade`. Aggregates the dependencies a module
may need at install/upgrade time without bleeding the full app surface.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.core.events.bus import EventBus


@dataclass
class ModuleContext:
    """Runtime context passed to lifecycle hooks."""

    module_name: str
    db: AsyncSession
    event_bus: EventBus
    logger: logging.Logger
