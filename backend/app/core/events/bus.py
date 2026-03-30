"""Event bus for cross-module communication."""
import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)

Handler = Callable[[dict[str, Any]], None]


class EventBus:
    """Simple synchronous event bus.

    Modules can subscribe to events and publish events.
    For MVP, handlers run synchronously and errors are logged but don't propagate.
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

        For MVP, this logs the event. Handlers are called synchronously
        and errors are logged but don't propagate to the caller.
        """
        logger.info(f"Event published: {event_type}", extra={"event_data": data})

        handlers = self._handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(data)
            except Exception as e:
                logger.error(
                    f"Error in event handler for {event_type}: {e}",
                    exc_info=True,
                )

    def clear(self) -> None:
        """Remove all handlers. Useful for testing."""
        self._handlers.clear()


# Global singleton instance
event_bus = EventBus()
