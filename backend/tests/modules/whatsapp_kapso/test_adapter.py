"""KapsoAdapter unit tests (Kapso HTTP mocked)."""

import pytest

from app.core.email.encryption import encrypt_password
from app.modules.notifications.channels import Channel, OutboundMessage, SendStatus
from app.modules.whatsapp_kapso import client as kapso_client
from app.modules.whatsapp_kapso.adapter import KapsoAdapter
from app.modules.whatsapp_kapso.models import WhatsappKapsoSettings


async def _settings(db, clinic_id):
    s = WhatsappKapsoSettings(
        clinic_id=clinic_id,
        api_key_encrypted=encrypt_password("api-key"),
        phone_number_id="PNID",
        webhook_secret_encrypted=encrypt_password("secret"),
        is_active=True,
    )
    db.add(s)
    await db.commit()
    return s


def _msg(clinic_id, *, kind="template", **kw):
    base = dict(
        channel=Channel.WHATSAPP,
        to_address="+34600111222",
        clinic_id=clinic_id,
        template_key="appointment_reminder",
        locale="es",
        context={"patient_name": "Ana"},
        message_kind=kind,
    )
    base.update(kw)
    return OutboundMessage(**base)


@pytest.mark.asyncio
async def test_template_send_returns_wamid(db_session, test_clinic, monkeypatch):
    await _settings(db_session, test_clinic.id)
    captured = {}

    async def fake_send(api_key, pnid, payload):
        captured["payload"] = payload
        return {"messages": [{"id": "wamid.abc"}]}

    monkeypatch.setattr(kapso_client, "send_message", fake_send)
    res = await KapsoAdapter().send(
        db_session, _msg(test_clinic.id, provider_template_name="recordatorio")
    )
    assert res.status == SendStatus.SENT
    assert res.provider_message_id == "wamid.abc"
    assert captured["payload"]["type"] == "template"
    assert captured["payload"]["template"]["name"] == "recordatorio"


@pytest.mark.asyncio
async def test_session_text_send(db_session, test_clinic, monkeypatch):
    await _settings(db_session, test_clinic.id)

    async def fake_send(api_key, pnid, payload):
        assert payload["type"] == "text"
        assert payload["text"]["body"] == "Hola, le confirmo"
        return {"messages": [{"id": "wamid.txt"}]}

    monkeypatch.setattr(kapso_client, "send_message", fake_send)
    res = await KapsoAdapter().send(
        db_session, _msg(test_clinic.id, kind="session", body_text="Hola, le confirmo")
    )
    assert res.status == SendStatus.SENT


@pytest.mark.asyncio
async def test_kapso_error_maps_to_failed(db_session, test_clinic, monkeypatch):
    await _settings(db_session, test_clinic.id)

    async def boom(*a, **k):
        raise kapso_client.KapsoError("Kapso returned HTTP 422: code 131047 outside window")

    monkeypatch.setattr(kapso_client, "send_message", boom)
    res = await KapsoAdapter().send(
        db_session, _msg(test_clinic.id, kind="session", body_text="late")
    )
    assert res.status == SendStatus.FAILED
    assert "131047" in res.error_message


@pytest.mark.asyncio
async def test_supports_requires_active_settings(db_session, test_clinic):
    adapter = KapsoAdapter()
    assert await adapter.supports(db_session, test_clinic.id) is False
    await _settings(db_session, test_clinic.id)
    assert await adapter.supports(db_session, test_clinic.id) is True
