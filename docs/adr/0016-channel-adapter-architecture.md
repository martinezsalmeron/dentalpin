# 0016 — Channel-adapter architecture for the notifications gateway

- **Status:** accepted
- **Date:** 2026-06-26
- **Deciders:** Backend team
- **Tags:** modules, notifications, events, integrations

## Context

The `notifications` module was email-only and sent synchronously inside the
request (`service.send_notification`), which its own `CLAUDE.md` flagged as a
gotcha ("no outbound network calls during a request"). The clinic market
(ES/LATAM) needs WhatsApp, delivered through a third-party vendor (Kapso, with
Twilio as an alternative) — issue #63. We want our own communications logic in
core and a thin, swappable adapter for the wire, without coupling the core
module to any vendor and without breaking module isolation.

## Decision

The **channel-adapter contract and registry live inside `notifications`**
(`backend/app/modules/notifications/channels/`), not in core. A vendor module
declares `depends=["notifications"]`, imports the public contract, and
**registers its adapter at import time** via `channel_registry.register(...)`.
Delivery goes through a **durable outbox**: `enqueue` persists a `queued`
`communication_messages` row (committing with the request) and a scheduled
`dispatch_outbox` job sends it with `FOR UPDATE SKIP LOCKED` + exponential
backoff. **Vendor secrets live in the vendor module's own table/branch**, never
in core; core only records which adapter serves which channel per clinic
(`clinic_channel_settings`, non-secret).

## Consequences

### Good

- Adding a channel is a new community module + one `register()` call — zero
  core changes, passes `test_module_isolation.py` (only import is
  `app.modules.notifications.channels`, which is in the vendor's `depends`).
- No network in the request transaction; sends are retriable and observable
  (status lifecycle on one row that is both queue entry and audit record).
- Clean round-trip uninstall: dropping the vendor module drops its secrets and
  its adapter unregisters; the channel simply falls back to email.
- The outbox + registry are reusable substrate for future fan-out (telephony
  #64, public webhooks #65) — to be extracted to core only when a second real
  consumer exists (avoid speculative generalization now).

### Bad / accepted trade-offs

- Import-time registration is an import side-effect (the codebase otherwise
  prefers explicit `BaseModule` hooks). Mitigated by dependency-ordered loading
  (`topological_sort`) + idempotent `register`.
- A process crash mid-send can leave a row in `sending` (visible in the logs
  view). Upgrade path: sweep stale `sending` rows back to `failed`.
- WhatsApp proactive sends are template-only (Meta 24h-window rule) in V1.

## Alternatives considered

- **Core-level `BaseModule.get_channel_adapters()` hook** — more idiomatic (no
  import side-effect) but puts notification-flavoured types (`OutboundMessage`)
  in core before a second consumer exists. Rejected as premature coupling.
- **Vendor adapter in-core (no separate module)** — simpler install but violates
  "non-core modules ship off, admin activates" and bloats the core module with
  vendor HTTP + secrets. Rejected.
- **Keep synchronous send, add a WhatsApp branch** — no durability/retry and
  keeps network in the request. Rejected.

## How to verify the rule still holds

- `backend/tests/test_module_isolation.py` — fails if a vendor adapter imports
  anything outside its `depends`.
- `backend/tests/test_notifications_gateway.py` — adapter contract, registry
  idempotency/unregister, outbox dispatch + backoff, consent hard-block.
- Round-trip uninstall test for the vendor module (`whatsapp_kapso`, Phase 2).

## References

- `backend/app/modules/notifications/channels/` (contract + registry)
- `backend/app/modules/notifications/gateway.py` (enqueue + dispatch)
- `backend/app/modules/notifications/models.py` (`communication_messages`)
- Issue #63; ADRs 0001 (modular contract), 0003 (event bus)
