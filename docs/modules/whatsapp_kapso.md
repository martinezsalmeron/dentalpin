# whatsapp_kapso

WhatsApp delivery for the notifications gateway via **Kapso** (SaaS over the
Meta WhatsApp Cloud API). Community, installable/removable. Issue #63.

It is the thin vendor adapter under [ADR 0016](../adr/0016-channel-adapter-architecture.md):
a `KapsoAdapter` registered into the notifications channel registry, a public
signed webhook (delivery status + inbound replies), and a connect/settings UI
(credentials, template sync + mapping, test send). All comms logic — routing,
consent, outbox, the conversation thread and 24h session window — lives in
`notifications` ([ADR 0017](../adr/0017-inbound-conversation.md)).

- Technical: [`docs/technical/whatsapp_kapso/`](../technical/whatsapp_kapso/overview.md)
- User manual: [`docs/user-manual/es/whatsapp_kapso/`](../user-manual/es/whatsapp_kapso/index.md)
- Per-module notes: `backend/app/modules/whatsapp_kapso/CLAUDE.md`

**Prerequisite (legal/ops, not code):** a signed DPA with Kapso (data
processor) and, per clinic, a WhatsApp Business Account with Meta billing.
