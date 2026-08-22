"""Thin outbound HTTP client for webhook deliveries.

Isolated from ``gateway.py`` so tests can ``monkeypatch.setattr`` this
one function instead of patching httpx internals — same pattern as
``whatsapp_kapso.client.send_message`` (mirrors
``verifactu/services/aeat_client.py``: an ``httpx.AsyncClient`` per
call with a timeout, mapping transport errors to one exception type).
"""

from __future__ import annotations

import httpx

from .url_safety import UnsafeWebhookURLError, validate_before_dispatch

_REQUEST_TIMEOUT = 10.0


class WebhookDeliveryError(Exception):
    """Transport-level failure delivering a webhook (no HTTP response)."""


async def post_webhook(url: str, body: bytes, headers: dict[str, str]) -> httpx.Response:
    """POST ``body`` to ``url``. Raises :class:`WebhookDeliveryError` on any
    transport failure (including a URL that now fails the SSRF check — a
    subscription's target_url is re-validated here, not just at creation,
    since a hostname can be repointed after the subscription was created);
    a non-2xx HTTP response is returned normally — the caller decides how
    to treat the status code."""
    try:
        validate_before_dispatch(url)
    except UnsafeWebhookURLError as exc:
        raise WebhookDeliveryError(f"unsafe target_url: {exc}") from exc
    try:
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT, follow_redirects=False) as client:
            return await client.post(url, content=body, headers=headers)
    except httpx.HTTPError as exc:
        raise WebhookDeliveryError(str(exc)) from exc
