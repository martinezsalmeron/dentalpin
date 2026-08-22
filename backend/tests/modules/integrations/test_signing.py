"""Outbound webhook signing — Stripe-exact scheme (sign/verify)."""

import hashlib
import hmac
import time

import pytest

from app.modules.integrations.signing import sign, verify

SECRET = "whsec_test"
PAYLOAD = b'{"event":"patient.created","id":"abc"}'


def test_sign_verify_roundtrip():
    header = sign(SECRET, PAYLOAD)
    assert verify(SECRET, PAYLOAD, header)


def test_header_shape_matches_stripe():
    header = sign(SECRET, PAYLOAD, timestamp=1700000000)
    # t=<ts>,v1=<hex> — exact shape, not just "contains the parts".
    assert header.startswith("t=1700000000,v1=")
    ts_part, v1_part = header.split(",")
    assert ts_part == "t=1700000000"
    assert v1_part.startswith("v1=")
    mac = v1_part.removeprefix("v1=")
    assert len(mac) == 64  # hex sha256
    int(mac, 16)  # raises if not hex


def test_signed_string_is_timestamp_dot_payload():
    """The construction itself must be timestamp + '.' + raw body — not
    body-only, not JSON-re-encoded, not any other join."""
    ts = 1700000000
    header = sign(SECRET, PAYLOAD, timestamp=ts)
    mac = header.split("v1=")[1]
    expected = hmac.new(SECRET.encode(), f"{ts}.".encode() + PAYLOAD, hashlib.sha256).hexdigest()
    assert mac == expected


def test_wrong_secret_rejected():
    header = sign(SECRET, PAYLOAD)
    assert not verify("wrong_secret", PAYLOAD, header)


def test_tampered_payload_rejected():
    header = sign(SECRET, PAYLOAD)
    assert not verify(SECRET, PAYLOAD + b"x", header)


def test_expired_timestamp_rejected():
    old_ts = int(time.time()) - 301  # just past the 5-minute tolerance
    header = sign(SECRET, PAYLOAD, timestamp=old_ts)
    assert not verify(SECRET, PAYLOAD, header)


def test_timestamp_within_tolerance_accepted():
    ts = int(time.time()) - 299
    header = sign(SECRET, PAYLOAD, timestamp=ts)
    assert verify(SECRET, PAYLOAD, header)


def test_future_timestamp_beyond_tolerance_rejected():
    # Clock skew can push a legit delivery slightly ahead; abs() must
    # reject far-future the same as far-past.
    future_ts = int(time.time()) + 301
    header = sign(SECRET, PAYLOAD, timestamp=future_ts)
    assert not verify(SECRET, PAYLOAD, header)


@pytest.mark.parametrize(
    "bad_header",
    [
        "",
        "garbage",
        "t=1700000000",  # missing v1
        "v1=deadbeef",  # missing t
        "t=notanumber,v1=deadbeef",
        "t=1700000000,v1=",
    ],
)
def test_malformed_header_rejected(bad_header):
    assert not verify(SECRET, PAYLOAD, bad_header)


def test_body_only_hmac_does_not_verify_against_our_header():
    """Regression guard: a body-only HMAC (the old inbound
    whatsapp_kapso shape, no timestamp) must NOT satisfy `verify` —
    proves the timestamp is actually part of the signed string, not
    decorative. If this ever passes, the construction silently
    degraded to body-only signing."""
    body_only_mac = hmac.new(SECRET.encode(), PAYLOAD, hashlib.sha256).hexdigest()
    fake_header = f"t={int(time.time())},v1={body_only_mac}"
    assert not verify(SECRET, PAYLOAD, fake_header)
