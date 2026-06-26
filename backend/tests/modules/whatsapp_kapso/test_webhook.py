"""whatsapp_kapso public webhook tests (signature, routing, inbound)."""

import hashlib
import hmac
import json

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.email.encryption import encrypt_password
from app.modules.notifications.models import CommunicationMessage
from app.modules.whatsapp_kapso.models import WhatsappKapsoSettings

WEBHOOK = "/api/v1/whatsapp_kapso/webhook"


async def _settings(db, clinic_id, *, pnid, secret):
    db.add(
        WhatsappKapsoSettings(
            clinic_id=clinic_id,
            api_key_encrypted=encrypt_password("k"),
            phone_number_id=pnid,
            webhook_secret_encrypted=encrypt_password(secret),
            is_active=True,
        )
    )
    await db.commit()


def _signed(payload: dict, secret: str) -> tuple[bytes, str]:
    raw = json.dumps(payload).encode()
    sig = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    return raw, sig


@pytest.mark.asyncio
async def test_inbound_records_reply(client: AsyncClient, db_session: AsyncSession, test_patient):
    await _settings(db_session, test_patient.clinic_id, pnid="PNID1", secret="whsec")
    payload = {
        "phone_number_id": "PNID1",
        "message": {
            "id": "wamid.in.99",
            "from": test_patient.phone,
            "type": "text",
            "text": {"body": "Confirmo mi cita"},
            "kapso": {"direction": "inbound", "content": "Confirmo mi cita"},
        },
    }
    raw, sig = _signed(payload, "whsec")
    resp = await client.post(
        WEBHOOK,
        content=raw,
        headers={"X-Webhook-Signature": sig, "Content-Type": "application/json"},
    )
    assert resp.status_code == 200
    row = (
        await db_session.execute(
            select(CommunicationMessage).where(CommunicationMessage.dedup_key == "wamid.in.99")
        )
    ).scalar_one()
    assert row.direction == "inbound"
    assert row.body_text == "Confirmo mi cita"
    assert row.patient_id == test_patient.id


@pytest.mark.asyncio
async def test_bad_signature_rejected(client: AsyncClient, db_session: AsyncSession, test_clinic):
    await _settings(db_session, test_clinic.id, pnid="PNID2", secret="realsecret")
    payload = {
        "phone_number_id": "PNID2",
        "message": {"id": "x", "kapso": {"direction": "inbound"}},
    }
    raw = json.dumps(payload).encode()
    resp = await client.post(WEBHOOK, content=raw, headers={"X-Webhook-Signature": "deadbeef"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_unknown_number_accepted_and_ignored(client: AsyncClient):
    raw = json.dumps({"phone_number_id": "UNKNOWN", "message": {}}).encode()
    resp = await client.post(WEBHOOK, content=raw, headers={"X-Webhook-Signature": "whatever"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_delivery_status_updates_message(
    client: AsyncClient, db_session: AsyncSession, test_patient
):
    await _settings(db_session, test_patient.clinic_id, pnid="PNID3", secret="s3")
    # an outbound message awaiting a delivery receipt
    sent = CommunicationMessage(
        clinic_id=test_patient.clinic_id,
        channel="whatsapp",
        to_address=test_patient.phone,
        patient_id=test_patient.id,
        template_key="appointment_reminder",
        status="sent",
        provider="whatsapp_kapso",
        provider_message_id="wamid.out.1",
    )
    db_session.add(sent)
    await db_session.commit()

    payload = {
        "phone_number_id": "PNID3",
        "message": {"id": "wamid.out.1", "kapso": {"direction": "outbound", "status": "delivered"}},
    }
    raw, sig = _signed(payload, "s3")
    resp = await client.post(WEBHOOK, content=raw, headers={"X-Webhook-Signature": sig})
    assert resp.status_code == 200
    await db_session.refresh(sent)
    assert sent.status == "delivered"
    assert sent.delivered_at is not None
