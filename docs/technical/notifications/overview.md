---
module: notifications
last_verified_commit: 0000000
---

# Notifications — technical overview

> _Scaffolded stub — replace with proper documentation when this module is next touched._

Auto-discovered facts about the `notifications` module. See the module's
own notes at `backend/app/modules/notifications/CLAUDE.md` for context
the scaffold could not infer.

## API surface

- `DELETE /api/v1/notifications/templates/{template_id}`
- `GET /api/v1/notifications/logs`
- `GET /api/v1/notifications/preferences/patient/{patient_id}`
- `GET /api/v1/notifications/settings`
- `GET /api/v1/notifications/smtp-settings`
- `GET /api/v1/notifications/templates`
- `GET /api/v1/notifications/templates/{template_id}`
- `POST /api/v1/notifications/send`
- `POST /api/v1/notifications/smtp-settings/test`
- `POST /api/v1/notifications/templates`
- `POST /api/v1/notifications/test`
- `PUT /api/v1/notifications/preferences/patient/{patient_id}`
- `PUT /api/v1/notifications/settings`
- `PUT /api/v1/notifications/smtp-settings`
- `PUT /api/v1/notifications/templates/{template_id}`

## Frontend

- `backend/app/modules/notifications/frontend/pages/settings/notifications.vue` → `/settings/notifications`

## Permissions

`templates.read`, `templates.write`, `preferences.read`, `preferences.write`, `logs.read`, `send`, `settings.read`, `settings.write`

See [`./permissions.md`](./permissions.md) for the full role mapping.

## Events

- **Emits:** _(none)_
- **Subscribes:** `appointment.cancelled`, `appointment.scheduled`, `budget.accepted`, `budget.sent`, `invoice.sent`, `patient.created`

See [`./events.md`](./events.md) for the per-event detail (when the
module participates in the event bus).

## See also

- Module CLAUDE notes: `backend/app/modules/notifications/CLAUDE.md`
- [Documentation portal contract](../../technical/documentation-portal.md)
