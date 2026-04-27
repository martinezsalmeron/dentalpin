"""Generic ``compliance_severity`` filter on the invoice list endpoint.

Billing knows nothing about Verifactu — it just filters on
``compliance_data.<country>.severity`` via JSONB. These tests use ES as
the country but the implementation must stay country-agnostic.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic
from app.modules.billing.models import Invoice
from app.modules.patients.models import Patient


async def _make_invoice(
    db: AsyncSession,
    clinic: Clinic,
    patient: Patient,
    user_id,
    *,
    severity: str | None,
    number: str,
) -> Invoice:
    cd = None
    if severity is not None:
        cd = {"ES": {"state": "rejected", "severity": severity}}
    inv = Invoice(
        id=uuid4(),
        clinic_id=clinic.id,
        patient_id=patient.id,
        invoice_number=number,
        sequential_number=int(number.split("-")[-1]),
        status="issued",
        issue_date=date.today(),
        billing_name="X",
        billing_tax_id="A28000000",
        subtotal=Decimal("100"),
        total=Decimal("100"),
        balance_due=Decimal("100"),
        compliance_data=cd,
        created_by=user_id,
        issued_by=user_id,
    )
    db.add(inv)
    await db.flush()
    return inv


@pytest.mark.asyncio
async def test_compliance_severity_filter_returns_only_matching(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_clinic: Clinic,
    test_patient: Patient,
    db_session: AsyncSession,
) -> None:
    me = await client.get("/api/v1/auth/me", headers=auth_headers)
    user_id = me.json()["data"]["user"]["id"]

    await _make_invoice(db_session, test_clinic, test_patient, user_id, severity="ok", number="FAC-2026-0001")
    await _make_invoice(db_session, test_clinic, test_patient, user_id, severity="error", number="FAC-2026-0002")
    await _make_invoice(db_session, test_clinic, test_patient, user_id, severity=None, number="FAC-2026-0003")
    await db_session.commit()

    r_all = await client.get("/api/v1/billing/invoices", headers=auth_headers)
    assert r_all.status_code == 200
    assert r_all.json()["total"] == 3

    r_err = await client.get(
        "/api/v1/billing/invoices?compliance_severity=error", headers=auth_headers
    )
    assert r_err.status_code == 200
    items = r_err.json()["data"]
    assert len(items) == 1
    assert items[0]["invoice_number"] == "FAC-2026-0002"
    # compliance_data exposed in list response.
    assert items[0]["compliance_data"]["ES"]["severity"] == "error"


@pytest.mark.asyncio
async def test_compliance_severity_multivalue(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_clinic: Clinic,
    test_patient: Patient,
    db_session: AsyncSession,
) -> None:
    me = await client.get("/api/v1/auth/me", headers=auth_headers)
    user_id = me.json()["data"]["user"]["id"]

    await _make_invoice(db_session, test_clinic, test_patient, user_id, severity="ok", number="FAC-2026-0010")
    await _make_invoice(db_session, test_clinic, test_patient, user_id, severity="warning", number="FAC-2026-0011")
    await _make_invoice(db_session, test_clinic, test_patient, user_id, severity="error", number="FAC-2026-0012")
    await db_session.commit()

    r = await client.get(
        "/api/v1/billing/invoices?compliance_severity=error&compliance_severity=warning",
        headers=auth_headers,
    )
    assert r.status_code == 200
    nums = sorted(i["invoice_number"] for i in r.json()["data"])
    assert nums == ["FAC-2026-0011", "FAC-2026-0012"]


@pytest.mark.asyncio
async def test_compliance_severity_invalid_value_rejected(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    r = await client.get(
        "/api/v1/billing/invoices?compliance_severity=catastrophic",
        headers=auth_headers,
    )
    assert r.status_code == 422
    assert "compliance_severity" in r.json()["detail"].lower() or "catastrophic" in str(r.json())
