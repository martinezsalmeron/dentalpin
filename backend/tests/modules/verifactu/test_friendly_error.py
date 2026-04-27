"""Tagged AEAT error mapping (field + suggested CTA)."""

from __future__ import annotations

import pytest

from app.modules.verifactu.services.error_messages import (
    friendly_error,
    friendly_message,
)


def test_friendly_error_for_4116_targets_clinic() -> None:
    err = friendly_error(4116)
    assert err["field"] == "emisor"
    assert err["suggested_cta"] == "edit_clinic"
    assert "NIF" in err["message"]


@pytest.mark.parametrize("code", [4117, 4140])
def test_friendly_error_destinatario_codes(code: int) -> None:
    err = friendly_error(code)
    assert err["field"] == "destinatario"
    assert err["suggested_cta"] == "edit_billing_party"


def test_friendly_error_for_1237_lines() -> None:
    err = friendly_error(1237)
    assert err["field"] == "linea"
    assert err["suggested_cta"] == "edit_lines"


def test_friendly_error_for_chain_break_3000() -> None:
    err = friendly_error(3000)
    assert err["field"] == "cadena"
    assert err["suggested_cta"] == "contact_support"


def test_friendly_error_unknown_falls_back() -> None:
    err = friendly_error(9999, "raw aeat description")
    assert err["field"] is None
    assert err["suggested_cta"] == "contact_support"
    assert "raw aeat" in err["message"]


def test_friendly_error_none_uses_fallback() -> None:
    err = friendly_error(None, "fallback text")
    assert err["message"] == "fallback text"
    assert err["field"] is None


def test_friendly_message_back_compat_returns_string() -> None:
    assert friendly_message(4116) is not None
    assert friendly_message(None, "x") == "x"
    assert friendly_message(9999, None) is None
