"""KapsoAdapter — delivers the WhatsApp channel via Kapso.

Implements the notifications ``ChannelAdapter`` contract (the only cross-module
import; legal because ``notifications`` is in this module's ``depends``). Pure
wire: load per-clinic creds, build the Kapso payload, map the response to an
``AdapterResult``. No business logic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select

from app.core.email.encryption import decrypt_password
from app.modules.notifications.channels import (
    AdapterResult,
    Channel,
    OutboundMessage,
    SendStatus,
)

from . import client
from .models import WhatsappKapsoSettings

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def _active_settings(db: AsyncSession, clinic_id: UUID) -> WhatsappKapsoSettings | None:
    return (
        await db.execute(
            select(WhatsappKapsoSettings).where(
                WhatsappKapsoSettings.clinic_id == clinic_id,
                WhatsappKapsoSettings.is_active.is_(True),
            )
        )
    ).scalar_one_or_none()


class KapsoAdapter:
    """WhatsApp delivery via Kapso (Meta Cloud API)."""

    channel = Channel.WHATSAPP
    adapter_name = "whatsapp_kapso"

    async def supports(self, db: AsyncSession, clinic_id: UUID) -> bool:
        return await _active_settings(db, clinic_id) is not None

    async def send(self, db: AsyncSession, msg: OutboundMessage) -> AdapterResult:
        settings = await _active_settings(db, msg.clinic_id)
        if settings is None:
            return AdapterResult(
                status=SendStatus.FAILED,
                provider=self.adapter_name,
                error_message="whatsapp_kapso not configured for this clinic",
            )

        api_key = decrypt_password(settings.api_key_encrypted)
        if not api_key:
            return AdapterResult(
                status=SendStatus.FAILED,
                provider=self.adapter_name,
                error_message="could not decrypt Kapso api key",
            )

        if msg.message_kind == "session":
            payload = client.text_payload(msg.to_address, msg.body_text or "")
        else:
            payload = client.template_payload(
                to=msg.to_address,
                name=msg.provider_template_name or msg.template_key,
                language=msg.locale,
                components=client.build_named_components(msg.context),
            )

        try:
            data = await client.send_message(api_key, settings.phone_number_id, payload)
        except client.KapsoError as exc:
            return AdapterResult(
                status=SendStatus.FAILED, provider=self.adapter_name, error_message=str(exc)[:500]
            )

        wamid = ((data.get("messages") or [{}])[0] or {}).get("id")
        return AdapterResult(
            status=SendStatus.SENT, provider=self.adapter_name, provider_message_id=wamid
        )
