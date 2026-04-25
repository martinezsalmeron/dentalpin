"""Event handlers subscribed via :meth:`VerifactuModule.get_event_handlers`."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


async def on_invoice_paid(data: dict) -> None:
    """Placeholder. Currently AEAT does not require payment reporting
    for Veri*Factu — the registration covers the issuing event. We hook
    it here so we can extend later (e.g., suplido reporting)."""

    logger.debug("verifactu: invoice.paid received: %s", data.get("invoice_id"))
