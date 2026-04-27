# Treatment plan module

Patient treatment plans with budget + odontogram sync. **Heaviest
`depends` in the system** — this module is an integration hub. Read
this file before changing any cross-module flow.

## Public API

Routes mounted at `/api/v1/treatment-plans/`.

- `GET   /treatment-plans`              — list; `treatment_plan.plans.read`
- `POST  /treatment-plans`              — create; `treatment_plan.plans.write`
- `GET   /treatment-plans/{id}`         — detail
- `PUT   /treatment-plans/{id}`         — update; status transitions
- `POST  /treatment-plans/{id}/items`   — add item from catalog or odontogram tooth treatment
- `PUT   /treatment-plans/{id}/items/reorder`
- `POST  /treatment-plans/{id}/items/{item_id}/complete`
- Notes:  `treatment_plan.notes.{read,write}` on `/.../notes`, `/.../items/{id}/notes`

## Dependencies

`manifest.depends = ["patients", "agenda", "odontogram", "catalog", "budget", "media"]`.
Six dependencies. Anything not on this list is off-limits — no imports,
no FKs.

## Permissions

`treatment_plan.plans.{read,write}`,
`treatment_plan.notes.{read,write}`.

## Events emitted

| Event | When | Notes |
|---|---|---|
| `treatment_plan.created` | plan created | consumed by `patient_timeline` |
| `treatment_plan.status_changed` | status transition | currently no subscribers |
| `treatment_plan.treatment_added` | item added | consumed by `budget` (sync) |
| `treatment_plan.treatment_removed` | item removed | consumed by `budget` (sync) |
| `treatment_plan.treatment_completed` | item marked done | consumed by `patient_timeline` |
| `treatment_plan.budget_sync_requested` | manual resync | consumed by `budget` |
| `treatment_plan.plan_note_created` | plan-level clinical note | consumed by `patient_timeline` |
| `treatment_plan.item_note_created` | item-level clinical note | consumed by `patient_timeline` |
| `treatment_plan.item_completed_without_note` | completion check | consumed by `patient_timeline` |

> Two literals — `treatment_plan.items_reordered` (`service.py:515`)
> and `treatment_plan.unlocked` (`service.py:801`) — are still
> string-only. Adding them to `EventType` is a TODO; the events
> catalog surfaces them under "missing from EventType enum".

## Events consumed

| Event | Handler | Effect |
|---|---|---|
| `appointment.completed`         | `on_appointment_completed`  | mark planned items as performed if linked |
| `budget.accepted`               | `on_budget_accepted`        | sync plan ↔ budget state |
| `odontogram.treatment.performed` | `on_treatment_performed`   | mark planned item completed when its tooth treatment is performed |

## Lifecycle

- `removable=False`. Plans tie patients ↔ budgets ↔ tooth treatments;
  removing the module would orphan all three.

## Gotchas

- **Don't import budget/odontogram services directly for writes.**
  Use the event bus. Reads against modules in `depends` are OK.
- **Plan ↔ budget sync goes through events**, not direct calls. Adding
  a treatment to a plan publishes `treatment_plan.treatment_added`;
  the budget module's handler creates the matching budget line.
- **Item completion has two paths**: the user marks an item complete
  here, or the odontogram fires `odontogram.treatment.performed`. Both
  must converge to the same state — keep them idempotent.
- **Notes have an integrity rule**: completing an item without a
  clinical note publishes `treatment_plan.item_completed_without_note`
  for `patient_timeline` to surface in the audit feed. Don't bypass.

## Related ADRs

- `docs/adr/0001-modular-plugin-architecture.md`
- `docs/adr/0003-event-bus-over-direct-imports.md`

## CHANGELOG

See `./CHANGELOG.md`.
