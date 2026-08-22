"""POST /india-gst/tax-preview — stateless Decimal-safe preview."""

from __future__ import annotations

from httpx import AsyncClient

from app.modules.india_gst.models import IndiaGstSettings


async def test_tax_preview_intra_state(
    client: AsyncClient, auth_headers, india_gst_settings: IndiaGstSettings
):
    r = await client.post(
        "/api/v1/india_gst/tax-preview",
        json={
            "items": [{"vat_rate": "18", "line_tax": "1800.00"}],
            "place_of_supply": "33",
        },
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["is_intra"] is True
    assert data["cgst_total"] == "900.00"
    assert data["sgst_total"] == "900.00"


async def test_tax_preview_inter_state(
    client: AsyncClient, auth_headers, india_gst_settings: IndiaGstSettings
):
    r = await client.post(
        "/api/v1/india_gst/tax-preview",
        json={
            "items": [{"vat_rate": "18", "line_tax": "1800.00"}],
            "place_of_supply": "29",
        },
        headers=auth_headers,
    )
    data = r.json()["data"]
    assert data["is_intra"] is False
    assert data["igst_total"] == "1800.00"
