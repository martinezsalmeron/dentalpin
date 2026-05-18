"""Event bus for cross-module communication."""

import asyncio
import inspect
import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

Handler = Callable[[dict[str, Any]], None]


class EventBus:
    """Event bus with async handler support.

    Modules can subscribe to events and publish events.
    Supports both sync and async handlers. Handlers run inline — a
    publisher that ``await``s ``publish()`` is guaranteed every
    subscriber has finished before the call returns. Handler
    exceptions are caught and logged so one broken subscriber cannot
    fail another, but the publisher sees a clean return.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = {}

    def subscribe(self, event_type: str, handler: Handler) -> None:
        """Subscribe a handler to an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.debug(f"Handler subscribed to event: {event_type}")

    def unsubscribe(self, event_type: str, handler: Handler) -> None:
        """Unsubscribe a handler from an event type."""
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
            except ValueError:
                pass

    async def publish(self, event_type: str, data: dict[str, Any]) -> None:
        """Publish an event and await every subscriber to completion.

        Sync handlers run inline; async handlers are awaited in order.
        Handler exceptions are caught and logged — one failing
        subscriber does not abort the rest, and the publisher sees a
        clean return. The contract is: "after ``await``, every handler
        has finished (or failed)."

        Handlers that need fire-and-forget (e.g. an SMTP call that
        should not block the request) are responsible for scheduling
        their own background task internally.
        """
        logger.info(f"Event published: {event_type}", extra={"event_data": data})

        for handler in self._handlers.get(event_type, []):
            try:
                result = handler(data)
                if inspect.iscoroutine(result):
                    await result
            except Exception:
                logger.exception(
                    "Event handler %s failed for %s",
                    getattr(handler, "__qualname__", handler.__name__),
                    event_type,
                    extra={
                        "event_type": event_type,
                        "clinic_id": data.get("clinic_id"),
                    },
                )

    def publish_sync(self, event_type: str, data: dict[str, Any]) -> None:
        """Sync entry point for non-async callers (scripts, REPL).

        Avoid in production code — it spins up a fresh loop with
        ``asyncio.run`` and will fail inside an already-running loop.
        Always prefer ``await event_bus.publish(...)`` from async
        contexts.
        """
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(self.publish(event_type, data))
            return
        raise RuntimeError(
            "publish_sync called from a running event loop — use "
            "'await event_bus.publish(...)' instead."
        )

    def clear(self) -> None:
        """Remove all handlers. Useful for testing."""
        self._handlers.clear()


# Global singleton instance
event_bus = EventBus()
