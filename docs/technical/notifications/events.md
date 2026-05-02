---
module: notifications
last_verified_commit: 0000000
---

# Notifications — events

> _Scaffolded stub — replace with proper documentation when this module is next touched._

Per-module slice of [`docs/events-catalog.md`](../../events-catalog.md)
(auto-generated). Update both files when adding or removing events.

## Published

_This module does not publish any events._

## Subscribed

| Event | Handler | Effect |
|-------|---------|--------|
| `appointment.cancelled` | _Handler module path._ | _What it does in response._ |
| `appointment.scheduled` | _Handler module path._ | _What it does in response._ |
| `budget.accepted` | _Handler module path._ | _What it does in response._ |
| `budget.sent` | _Handler module path._ | _What it does in response._ |
| `invoice.sent` | _Handler module path._ | _What it does in response._ |
| `patient.created` | _Handler module path._ | _What it does in response._ |

## Adding a new event

1. Add the constant to `backend/app/core/events/types.py` (`EventType`).
2. Publish from a service method, after the DB commit succeeds.
3. Add the row to the table(s) above.
4. Run `python backend/scripts/generate_catalogs.py` to refresh the
   global catalog.
