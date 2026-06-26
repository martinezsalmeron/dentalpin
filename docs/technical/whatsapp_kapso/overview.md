---
module: whatsapp_kapso
last_verified_commit: 0000000
---

# whatsapp_kapso — overview

WhatsApp delivery for the notifications gateway via **Kapso** (a SaaS over the
Meta WhatsApp Cloud API). Community module, installable/removable. Issue #63.

## What it is

The thin vendor "wire" under the channel-adapter architecture (ADR 0016):

- **`KapsoAdapter`** registers into `notifications.channels.channel_registry` at
  import time and delivers the `whatsapp` channel (template HSM or free-form
  text). Unregisters on uninstall.
- **Public `/webhook`** receives Kapso events: delivery/read status and inbound
  patient messages. Verified by a per-clinic HMAC signature; the clinic is
  resolved by `phone_number_id`.
- **Connect/settings**: per-clinic credentials (Fernet-encrypted), template
  auto-sync, type→template mapping, test send.

All communications logic (channel resolution, consent, outbox, the conversation
thread + 24h session window) lives in `notifications` (ADR 0017). This module
owns no comms state.

## Data model

- `whatsapp_kapso_settings` — per clinic: `api_key_encrypted`, `phone_number_id`,
  `business_account_id`, `webhook_secret_encrypted`, `display_phone_number`,
  verification + sync timestamps.
- `whatsapp_kapso_templates` — cached Meta templates (name/language/status) for
  the mapping picker.

Both on the `whatsapp_kapso` Alembic branch (`wak_0001`), dropped cleanly on
uninstall.

## Kapso API (docs.kapso.ai)

- Send: `POST https://api.kapso.ai/meta/whatsapp/v24.0/{phone_number_id}/messages`,
  header `X-API-Key`. Response `messages[0].id` = `wamid`.
- Templates: `GET …/{business_account_id}/message_templates`.
- Webhook: `X-Webhook-Signature` = HMAC-SHA256(raw body); tenant key
  `phone_number_id`.

## Constraints

Proactive sends require an approved template (HSM); free-form only inside the
24h session window. Kapso is a data processor → DPA + per-clinic WABA.
