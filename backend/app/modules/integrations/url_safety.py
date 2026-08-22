"""SSRF guard for clinic-supplied webhook target URLs.

A ``WebhookSubscription.target_url`` is attacker-controllable (any
clinic admin can set it) and the server POSTs to it directly
(``client.post_webhook``). Without a check, that URL could point at
an internal service, the cloud metadata endpoint
(``169.254.169.254``), or loopback. Not part of the original design
doc (notes/dentalpin/65-integrations-api.md) — added as a required
part of Phase 1, not deferred, since it's a real vulnerability in the
outbox as originally scoped.

Two checkpoints, not one: ``validate_new_url`` runs at subscription
create/update (schemas.py); ``validate_before_dispatch`` runs again
immediately before each send (client.py). A hostname can be
repointed after a subscription is created — validating only once at
creation doesn't defend against DNS rebinding or a delayed re-point,
since deliveries can fire days after subscribe.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlsplit

ALLOWED_SCHEMES = frozenset({"https"})


class UnsafeWebhookURLError(ValueError):
    """Raised when a target URL fails the SSRF safety check."""


def _resolved_ips(hostname: str) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise UnsafeWebhookURLError(f"could not resolve host: {hostname}") from exc
    ips = []
    for family, _, _, _, sockaddr in infos:
        raw = sockaddr[0]
        try:
            ips.append(ipaddress.ip_address(raw))
        except ValueError:
            continue
    if not ips:
        raise UnsafeWebhookURLError(f"could not resolve host: {hostname}")
    return ips


def _is_unsafe(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def _check(url: str) -> None:
    parts = urlsplit(url)
    if parts.scheme not in ALLOWED_SCHEMES:
        raise UnsafeWebhookURLError(
            f"webhook target_url must use one of {sorted(ALLOWED_SCHEMES)}, got {parts.scheme!r}"
        )
    hostname = parts.hostname
    if not hostname:
        raise UnsafeWebhookURLError("webhook target_url has no hostname")

    # A raw IP literal in the URL still needs the same check — getaddrinfo
    # on a literal just echoes it back, but check directly first so the
    # error message is clearer.
    try:
        literal = ipaddress.ip_address(hostname)
    except ValueError:
        literal = None
    if literal is not None and _is_unsafe(literal):
        raise UnsafeWebhookURLError(
            f"webhook target_url resolves to a disallowed address: {literal}"
        )

    for ip in _resolved_ips(hostname):
        if _is_unsafe(ip):
            raise UnsafeWebhookURLError(
                f"webhook target_url resolves to a disallowed address: {ip}"
            )


def validate_new_url(url: str) -> None:
    """Run at subscription create/update. Raises :class:`UnsafeWebhookURLError`."""
    _check(url)


def validate_before_dispatch(url: str) -> None:
    """Run again immediately before each delivery attempt, to catch a
    hostname that was repointed after the subscription was created
    (DNS rebinding / delayed re-point). Same check, same errors."""
    _check(url)
