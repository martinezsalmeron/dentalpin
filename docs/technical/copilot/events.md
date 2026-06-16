---
module: copilot
last_verified_commit: 0000000
---

# Copilot — events

Per-module slice of [`docs/events-catalog.md`](../../events-catalog.md)
(auto-generated). Update both files when adding or removing events.

## Published

| Event | When | Payload keys |
|-------|------|--------------|
| `copilot.session.started` | A chat session is created (`POST /sessions`). | `clinic_id`, `conversation_id`, `user_id` |
| `copilot.session.ended` | A chat session is closed (`POST /sessions/{id}/end`). | `clinic_id`, `conversation_id` |
| `copilot.digest.sent` | The morning digest is emailed to a recipient. | `clinic_id`, `recipient_user_id`, `date`, `email_status` |

`copilot.tool.invoked` and `copilot.budget.threshold_reached` are declared
in `EventType` but reserved for the dashboards milestone — not published
in v1. (Every tool call is already recorded in `agent_audit_logs`.)

## Subscribed

| Event | Handler | Effect |
|-------|---------|--------|
| `appointment.cancelled` | `events.on_appointment_cancelled` | Create a `copilot_nudges` row ("fill the freed slot from recalls?"), deduped per appointment with a same-day TTL. Subscription only — no import of the publisher (ADR 0003). |

## Adding a new event

1. Add the constant to `backend/app/core/events/types.py` (`EventType`).
2. Publish from the router/service after the DB commit succeeds.
3. Add a row above and re-run `python backend/scripts/generate_catalogs.py`.
