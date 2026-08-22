---
module: india_gst
last_verified_commit: 0000000
---

# India GST — events

> _Scaffolded stub — replace with proper documentation when this module is next touched._

Per-module slice of [`docs/events-catalog.md`](../../events-catalog.md)
(auto-generated). Update both files when adding or removing events.

## Published

_This module does not publish any events._ GST compliance data is
written synchronously via `BillingComplianceHook` on invoice issuance,
not the event bus — same rationale as `verifactu` (deterministic
ordering at issue time). See `backend/app/modules/india_gst/hook.py`.

## Subscribed

_This module does not subscribe to any events._

## Adding a new event

1. Add the constant to `backend/app/core/events/types.py` (`EventType`)
   — a placeholder section for future india_gst events already exists
   there (e.g. for a real e-invoice-provider integration).
2. Publish from a service method after `flush()` — the bus runs handlers
   inline, *before* the request commits. Pass `db=db` so transactional
   subscribers can join the transaction (ADR 0019, issue #183).
3. Add the row to the table(s) above.
4. Run `python backend/scripts/generate_catalogs.py` to refresh the
   global catalog.
