# 0017 — Inbound replies + conversation thread in communication_messages

- **Status:** accepted
- **Date:** 2026-06-26
- **Deciders:** Backend team
- **Tags:** modules, notifications, whatsapp

## Context

Phase 2 adds WhatsApp (via the `whatsapp_kapso` vendor module) and the product
need to **reply to patients**, not just log outbound sends. WhatsApp is
two-way: patients message the clinic, and staff must answer within Meta's 24h
free-form session window (outside it, only approved templates). We need a place
to store inbound messages and a way to send free-form replies, without coupling
the comms core to the vendor.

## Decision

Inbound messages and free-form replies live in the **same
`communication_messages` table** as outbound (one conversation thread), via a
new `direction` column (`outbound`/`inbound`) and `body_text` (literal text).
The `notifications` gateway owns it: `record_inbound_reply` (idempotent on the
vendor message id, opens the 24h window via `NotificationPreference.last_inbound_at`,
publishes `notification.reply_received`) and a session-aware `enqueue`
(`message_kind="session"` is viable only while the window is open). The vendor
module only calls these gateway methods from its webhook — it never owns
conversation state.

## Consequences

### Good
- One source of truth per patient thread; trivially queryable for the
  conversation UI and the timeline.
- Channel-agnostic: SMS or any future two-way channel reuses it unchanged.
- `whatsapp_kapso` stays a thin wire; isolation holds (it depends on
  `notifications`, not vice-versa).

### Bad / accepted trade-offs
- `communication_messages` is now outbox + audit + inbound log — broader than a
  pure outbox, but still "the comms record for this clinic".
- Free-form replies are blocked outside the 24h window (a Meta rule, surfaced as
  a 409 the UI explains) — correct, not a limitation we can remove.
- `do_not_contact` also hard-blocks replies; answering a do-not-contact patient
  needs that flag cleared first (deliberate, conservative).

## Alternatives considered
- **Separate inbound table in `whatsapp_kapso`** — splits the thread across
  modules and couples the conversation UI to the vendor. Rejected.
- **Full chat/inbox subsystem** — realtime, assignment, multi-agent. Out of
  scope for v1; the per-patient thread + reply box answers the need.

## How to verify the rule still holds
- `backend/tests/test_notifications_gateway.py` — inbound records + opens
  window; reply within window enqueues session; reply outside window is blocked.
- `backend/tests/modules/whatsapp_kapso/test_webhook.py` — inbound webhook →
  inbound row; delivery status → row update.

## References
- `backend/app/modules/notifications/gateway.py` (`record_inbound_reply`, session window)
- `backend/app/modules/notifications/migrations/versions/notif_0003_inbound_conversation.py`
- ADR 0016 (channel adapters); Issue #63
