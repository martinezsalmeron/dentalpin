---
module: treatment_plan
last_verified_commit: 0000000
---

# Treatment Plan — events

> _Scaffolded stub — replace with proper documentation when this module is next touched._

Per-module slice of [`docs/events-catalog.md`](../../events-catalog.md)
(auto-generated). Update both files when adding or removing events.

## Published

| Event | When | Payload |
|-------|------|---------|
| `treatment_plan.budget_sync_requested` | _When does this fire?_ | _Payload keys._ |
| `treatment_plan.created` | _When does this fire?_ | _Payload keys._ |
| `treatment_plan.status_changed` | _When does this fire?_ | _Payload keys._ |
| `treatment_plan.treatment_added` | _When does this fire?_ | _Payload keys._ |
| `treatment_plan.treatment_completed` | _When does this fire?_ | _Payload keys._ |
| `treatment_plan.treatment_removed` | _When does this fire?_ | _Payload keys._ |

## Subscribed

| Event | Handler | Effect |
|-------|---------|--------|
| `appointment.completed` | _Handler module path._ | _What it does in response._ |
| `budget.accepted` | _Handler module path._ | _What it does in response._ |
| `budget.rejected` | _Handler module path._ | _What it does in response._ |
| `budget.renegotiated` | _Handler module path._ | _What it does in response._ |
| `odontogram.treatment.performed` | _Handler module path._ | _What it does in response._ |

## Adding a new event

1. Add the constant to `backend/app/core/events/types.py` (`EventType`).
2. Publish from a service method, after the DB commit succeeds.
3. Add the row to the table(s) above.
4. Run `python backend/scripts/generate_catalogs.py` to refresh the
   global catalog.
