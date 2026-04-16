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
    Supports both sync and async handlers. Errors are logged but don't propagate.
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

    def publish(self, event_type: str, data: dict[str, Any]) -> None:
        """Publish an event to all subscribed handlers.

        Supports both sync and async handlers. Async handlers are scheduled
        as background tasks. Errors are logged but don't propagate.
        """
        logger.info(f"Event published: {event_type}", extra={"event_data": data})

        handlers = self._handlers.get(event_type, [])
        for handler in handlers:
            try:
                result = handler(data)
                # Handle async handlers
                if inspect.iscoroutine(result):
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(self._run_async_handler(event_type, result))
                    except RuntimeError:
                        # No running loop, run synchronously
                        asyncio.run(result)
            except Exception as e:
                logger.error(
                    f"Error in event handler for {event_type}: {e}",
                    exc_info=True,
                )

    async def _run_async_handler(
        self, event_type: str, coro: Any
    ) -> None:
        """Run an async handler and log errors."""
        try:
            await coro
        except Exception as e:
            logger.error(
                f"Error in async event handler for {event_type}: {e}",
                exc_info=True,
            )

    def clear(self) -> None:
        """Remove all handlers. Useful for testing."""
        self._handlers.clear()


# Global singleton instance
event_bus = EventBus()
