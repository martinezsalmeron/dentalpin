"""Process-wide registry of channel adapters.

Vendor modules register their adapter here at import time (see the module's
``__init__.py``). The loader imports module packages in dependency order
(``topological_sort``), so ``notifications`` — and therefore the built-in
:class:`EmailAdapter` — is always registered before any vendor that depends
on it.

Registration is idempotent (unlike ``ModuleRegistry.register``): re-import
during the dev filesystem re-scan is a no-op, not an error.
"""

from __future__ import annotations

import logging

from .base import Channel, ChannelAdapter
from .email_adapter import EmailAdapter

logger = logging.getLogger(__name__)


class ChannelRegistry:
    """Maps a channel to its active adapter (last-writer-wins per channel)."""

    def __init__(self) -> None:
        self._adapters: dict[str, ChannelAdapter] = {}  # adapter_name -> adapter

    def register(self, adapter: ChannelAdapter) -> None:
        name = adapter.adapter_name
        existing = self._adapters.get(name)
        if existing is not None and type(existing) is type(adapter):
            return  # idempotent: same adapter re-registered on re-import
        if name in self._adapters:
            logger.info("Channel adapter %r re-registered (override)", name)
        self._adapters[name] = adapter

    def unregister(self, adapter_name: str) -> None:
        """Drop an adapter (called on vendor-module uninstall)."""
        self._adapters.pop(adapter_name, None)

    def get_for_channel(self, channel: Channel | str) -> ChannelAdapter | None:
        """Return the adapter handling ``channel``, or None.

        With multiple adapters for one channel the last registered wins —
        fine for v1 (one vendor per channel per deployment).
        """
        channel = Channel(channel)
        for adapter in reversed(list(self._adapters.values())):
            if adapter.channel == channel:
                return adapter
        return None

    def get_by_name(self, adapter_name: str) -> ChannelAdapter | None:
        return self._adapters.get(adapter_name)

    def available_channels(self) -> list[Channel]:
        return sorted({a.channel for a in self._adapters.values()})


# Global singleton. Email is always present.
channel_registry = ChannelRegistry()
channel_registry.register(EmailAdapter())
