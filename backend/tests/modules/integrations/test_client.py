"""client.post_webhook: dispatch-time SSRF re-check (url_safety.py)."""

import socket

import pytest

from app.modules.integrations.client import WebhookDeliveryError, post_webhook


@pytest.mark.asyncio
async def test_post_webhook_rejects_repointed_url(monkeypatch):
    """A subscription's target_url can pass the creation-time check and
    still fail here if the hostname now resolves internally — dispatch
    must not silently fall back to sending anyway."""

    def fake_getaddrinfo(host, port):
        return [(socket.AF_INET, None, None, "", ("127.0.0.1", 0))]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)

    with pytest.raises(WebhookDeliveryError, match="unsafe target_url"):
        await post_webhook("https://was-safe.example.com/hook", b"{}", {})
