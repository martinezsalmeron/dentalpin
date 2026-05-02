---
module: treatment_plan
last_verified_commit: 0000000
---

# Treatment Plan — technical overview

> _Scaffolded stub — replace with proper documentation when this module is next touched._

Auto-discovered facts about the `treatment_plan` module. See the module's
own notes at `backend/app/modules/treatment_plan/CLAUDE.md` for context
the scaffold could not infer.

## API surface

- `DELETE /api/v1/treatment_plan/treatment-plans/{plan_id}`
- `DELETE /api/v1/treatment_plan/treatment-plans/{plan_id}/items/{item_id}`
- `GET /api/v1/treatment_plan/treatment-plans`
- `GET /api/v1/treatment_plan/treatment-plans/patient/{patient_id}`
- `GET /api/v1/treatment_plan/treatment-plans/pipeline`
- `GET /api/v1/treatment_plan/treatment-plans/{plan_id}`
- `PATCH /api/v1/treatment_plan/treatment-plans/{plan_id}/items/reorder`
- `PATCH /api/v1/treatment_plan/treatment-plans/{plan_id}/items/{item_id}/complete`
- `PATCH /api/v1/treatment_plan/treatment-plans/{plan_id}/status`
- `POST /api/v1/treatment_plan/treatment-plans`
- `POST /api/v1/treatment_plan/treatment-plans/{plan_id}/close`
- `POST /api/v1/treatment_plan/treatment-plans/{plan_id}/confirm`
- `POST /api/v1/treatment_plan/treatment-plans/{plan_id}/contact-log`
- `POST /api/v1/treatment_plan/treatment-plans/{plan_id}/generate-budget`
- `POST /api/v1/treatment_plan/treatment-plans/{plan_id}/items`
- `POST /api/v1/treatment_plan/treatment-plans/{plan_id}/link-budget`
- `POST /api/v1/treatment_plan/treatment-plans/{plan_id}/reactivate`
- `POST /api/v1/treatment_plan/treatment-plans/{plan_id}/reopen`
- `POST /api/v1/treatment_plan/treatment-plans/{plan_id}/sync-budget`
- `PUT /api/v1/treatment_plan/treatment-plans/{plan_id}`
- `PUT /api/v1/treatment_plan/treatment-plans/{plan_id}/items/{item_id}`

## Frontend

- `backend/app/modules/treatment_plan/frontend/pages/treatment-plans/index.vue` → `/treatment-plans`
- `backend/app/modules/treatment_plan/frontend/pages/treatment-plans/[id].vue` → `/treatment-plans/[id]`
- `backend/app/modules/treatment_plan/frontend/pages/treatment-plans/new.vue` → `/treatment-plans/new`

## Permissions

`plans.read`, `plans.write`, `plans.confirm`, `plans.close`, `plans.reactivate`

See [`./permissions.md`](./permissions.md) for the full role mapping.

## Events

- **Emits:** `treatment_plan.budget_sync_requested`, `treatment_plan.created`, `treatment_plan.status_changed`, `treatment_plan.treatment_added`, `treatment_plan.treatment_completed`, `treatment_plan.treatment_removed`
- **Subscribes:** `appointment.completed`, `budget.accepted`, `budget.rejected`, `budget.renegotiated`, `odontogram.treatment.performed`

See [`./events.md`](./events.md) for the per-event detail (when the
module participates in the event bus).

## See also

- Module CLAUDE notes: `backend/app/modules/treatment_plan/CLAUDE.md`
- [Documentation portal contract](../../technical/documentation-portal.md)
