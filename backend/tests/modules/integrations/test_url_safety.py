"""SSRF guard on webhook target_url — creation-time and dispatch-time."""

import socket

import pytest

from app.modules.integrations.url_safety import (
    UnsafeWebhookURLError,
    validate_before_dispatch,
    validate_new_url,
)


def test_rejects_non_https_scheme():
    with pytest.raises(UnsafeWebhookURLError, match="https"):
        validate_new_url("http://example.com/hook")


def test_rejects_loopback_ip_literal():
    with pytest.raises(UnsafeWebhookURLError, match="disallowed"):
        validate_new_url("https://127.0.0.1/hook")


def test_rejects_private_ip_literal():
    with pytest.raises(UnsafeWebhookURLError, match="disallowed"):
        validate_new_url("https://10.0.0.5/hook")


def test_rejects_cloud_metadata_ip_literal():
    with pytest.raises(UnsafeWebhookURLError, match="disallowed"):
        validate_new_url("https://169.254.169.254/latest/meta-data/")


def test_rejects_localhost_hostname(monkeypatch):
    def fake_getaddrinfo(host, port):
        assert host == "localhost"
        return [(socket.AF_INET, None, None, "", ("127.0.0.1", 0))]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    with pytest.raises(UnsafeWebhookURLError, match="disallowed"):
        validate_new_url("https://localhost/hook")


def test_rejects_hostname_that_resolves_to_link_local(monkeypatch):
    """Same category as cloud-metadata — a hostname (not just a raw IP
    literal) can resolve to 169.254.0.0/16."""

    def fake_getaddrinfo(host, port):
        return [(socket.AF_INET, None, None, "", ("169.254.169.254", 0))]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    with pytest.raises(UnsafeWebhookURLError, match="disallowed"):
        validate_new_url("https://metadata.internal/hook")


def test_rejects_unresolvable_hostname(monkeypatch):
    def fake_getaddrinfo(host, port):
        raise socket.gaierror("nope")

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    with pytest.raises(UnsafeWebhookURLError, match="could not resolve"):
        validate_new_url("https://does-not-exist.invalid/hook")


def test_accepts_public_https_hostname(monkeypatch):
    def fake_getaddrinfo(host, port):
        return [(socket.AF_INET, None, None, "", ("93.184.216.34", 0))]  # public

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    validate_new_url("https://example.com/hook")  # must not raise


def test_dispatch_time_check_catches_repointed_hostname(monkeypatch):
    """A subscription created against a safe IP can be repointed later
    (DNS rebinding / delayed re-point) — the dispatch-time check must
    catch it independently of the creation-time check."""

    def fake_getaddrinfo(host, port):
        return [(socket.AF_INET, None, None, "", ("10.0.0.9", 0))]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    with pytest.raises(UnsafeWebhookURLError, match="disallowed"):
        validate_before_dispatch("https://was-safe-now-internal.example.com/hook")
