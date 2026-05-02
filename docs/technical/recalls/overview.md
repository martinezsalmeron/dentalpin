---
module: recalls
last_verified_commit: 0000000
---

# Recalls — technical overview

> _Scaffolded stub — replace with proper documentation when this module is next touched._

Auto-discovered facts about the `recalls` module. See the module's
own notes at `backend/app/modules/recalls/CLAUDE.md` for context
the scaffold could not infer.

## API surface

- `DELETE /api/v1/recalls/{recall_id}`
- `GET /api/v1/recalls`
- `GET /api/v1/recalls/export.csv`
- `GET /api/v1/recalls/patients/{patient_id}`
- `GET /api/v1/recalls/settings`
- `GET /api/v1/recalls/stats/dashboard`
- `GET /api/v1/recalls/suggestions/next`
- `GET /api/v1/recalls/{recall_id}`
- `GET /api/v1/recalls/{recall_id}/attempts`
- `PATCH /api/v1/recalls/{recall_id}`
- `POST /api/v1/recalls`
- `POST /api/v1/recalls/{recall_id}/attempts`
- `POST /api/v1/recalls/{recall_id}/cancel`
- `POST /api/v1/recalls/{recall_id}/done`
- `POST /api/v1/recalls/{recall_id}/link-appointment`
- `POST /api/v1/recalls/{recall_id}/snooze`
- `PUT /api/v1/recalls/settings`

## Frontend

- `backend/app/modules/recalls/frontend/pages/recalls/index.vue` → `/recalls`

## Permissions

`read`, `write`, `delete`

See [`./permissions.md`](./permissions.md) for the full role mapping.

## Events

- **Emits:** _(none)_
- **Subscribes:** `appointment.cancelled`, `appointment.completed`, `appointment.scheduled`, `patient.archived`, `treatment_plan.treatment_completed`

See [`./events.md`](./events.md) for the per-event detail (when the
module participates in the event bus).

## See also

- Module CLAUDE notes: `backend/app/modules/recalls/CLAUDE.md`
- [Documentation portal contract](../../technical/documentation-portal.md)
