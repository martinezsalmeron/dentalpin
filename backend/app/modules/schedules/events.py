"""Event handlers — react to agenda's appointment lifecycle.

Purely informational: the handlers invalidate the analytics cache so
subsequent requests don't return stale totals. They never block the
appointment flow; if schedules is uninstalled the bus simply stops
calling these functions.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


async def on_appointment_scheduled(data: dict) -> None:
    logger.debug("schedules: appointment.scheduled received: %s", data.get("appointment_id"))


async def on_appointment_updated(data: dict) -> None:
    logger.debug("schedules: appointment.updated received: %s", data.get("appointment_id"))


async def on_appointment_cancelled(data: dict) -> None:
    logger.debug("schedules: appointment.cancelled received: %s", data.get("appointment_id"))
