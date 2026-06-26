---
module: whatsapp_kapso
last_verified_commit: 0000000
---

# whatsapp_kapso — events

This module **does not register event handlers and emits no events of its own**.
It drives the notifications gateway, which publishes the lifecycle events.

## Published (indirectly, via the notifications gateway)

| Event | Triggered when |
|-------|----------------|
| `notification.reply_received` | the webhook receives an inbound patient message → `NotificationGateway.record_inbound_reply` |
| `notification.delivered` | the webhook receives a delivered/read status → `NotificationGateway.record_delivery_status` |
| `notification.sent` / `notification.failed` | the outbox dispatches an outbound WhatsApp message through `KapsoAdapter` |

## Subscribed

None.

See [`docs/events-catalog.md`](../../events-catalog.md) for the global catalog
and `docs/technical/notifications/events.md` for the gateway side.
