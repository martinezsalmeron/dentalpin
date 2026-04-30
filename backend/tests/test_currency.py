"""Currency: helper + clinic-level setting + cross-module inheritance."""

from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic
from app.core.utils.currency import format_currency

# ---------------------------------------------------------------------------
# Helper: babel-backed format_currency
# ---------------------------------------------------------------------------


def test_format_currency_eur_es() -> None:
    out = format_currency(Decimal("1234.56"), "EUR", locale="es_ES")
    # Babel renders es_ES EUR with comma decimal + non-breaking space + €.
    assert "1234" in out.replace(".", "") or "1.234" in out
    assert "€" in out


def test_format_currency_usd_en() -> None:
    out = format_currency(Decimal("1234.56"), "USD", locale="en_US")
    assert out == "$1,234.56"


def test_format_currency_locale_dash_normalized() -> None:
    """``en-US`` (BCP 47) is accepted and normalized to ``en_US``."""
    out = format_currency(100, "USD", locale="en-US")
    assert out == "$100.00"


# ---------------------------------------------------------------------------
# Clinic currency PUT
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_clinic_currency_default_is_eur(
    db_session: AsyncSession, test_clinic: Clinic
) -> None:
    await db_session.refresh(test_clinic)
    assert test_clinic.currency == "EUR"


@pytest.mark.asyncio
async def test_update_clinic_currency_persists(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_clinic: Clinic,
    db_session: AsyncSession,
) -> None:
    response = await client.put(
        "/api/v1/auth/clinics",
        json={"currency": "USD"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["currency"] == "USD"

    db_session.expire_all()
    await db_session.refresh(test_clinic)
    assert test_clinic.currency == "USD"


@pytest.mark.asyncio
async def test_update_clinic_currency_rejects_invalid_iso(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_clinic: Clinic,
) -> None:
    response = await client.put(
        "/api/v1/auth/clinics",
        json={"currency": "euro"},  # not 3 uppercase letters
        headers=auth_headers,
    )
    assert response.status_code == 422
