---
module: verifactu
last_verified_commit: 0000000
---

# Verifactu — technical overview

> _Scaffolded stub — replace with proper documentation when this module is next touched._

Auto-discovered facts about the `verifactu` module. See the module's
own notes at `backend/app/modules/verifactu/CLAUDE.md` for context
the scaffold could not infer.

## API surface

- `DELETE /api/v1/verifactu/certificate/{cert_id}`
- `DELETE /api/v1/verifactu/producer/declaracion`
- `GET /api/v1/verifactu/certificate`
- `GET /api/v1/verifactu/certificate/history`
- `GET /api/v1/verifactu/health`
- `GET /api/v1/verifactu/nif-check`
- `GET /api/v1/verifactu/producer/defaults`
- `GET /api/v1/verifactu/queue`
- `GET /api/v1/verifactu/records`
- `GET /api/v1/verifactu/records/{record_id}`
- `GET /api/v1/verifactu/records/{record_id}/attempts`
- `GET /api/v1/verifactu/records/{record_id}/xml`
- `GET /api/v1/verifactu/settings`
- `GET /api/v1/verifactu/vat-mapping`
- `POST /api/v1/verifactu/certificate`
- `POST /api/v1/verifactu/queue/process-now`
- `POST /api/v1/verifactu/queue/retry-all`
- `POST /api/v1/verifactu/queue/{record_id}/retry`
- `PUT /api/v1/verifactu/producer`
- `PUT /api/v1/verifactu/settings`
- `PUT /api/v1/verifactu/vat-mapping/{vat_type_id}`

## Frontend

- `backend/app/modules/verifactu/frontend/pages/settings/verifactu/index.vue` → `/settings/verifactu`
- `backend/app/modules/verifactu/frontend/pages/settings/verifactu/certificate.vue` → `/settings/verifactu/certificate`
- `backend/app/modules/verifactu/frontend/pages/settings/verifactu/producer.vue` → `/settings/verifactu/producer`
- `backend/app/modules/verifactu/frontend/pages/settings/verifactu/queue.vue` → `/settings/verifactu/queue`
- `backend/app/modules/verifactu/frontend/pages/settings/verifactu/records.vue` → `/settings/verifactu/records`
- `backend/app/modules/verifactu/frontend/pages/settings/verifactu/vat-mapping.vue` → `/settings/verifactu/vat-mapping`

## Permissions

`settings.read`, `settings.configure`, `records.read`, `queue.manage`, `environment.promote`

See [`./permissions.md`](./permissions.md) for the full role mapping.

## Events

- **Emits:** _(none)_
- **Subscribes:** `invoice.paid`

See [`./events.md`](./events.md) for the per-event detail (when the
module participates in the event bus).

## See also

- Module CLAUDE notes: `backend/app/modules/verifactu/CLAUDE.md`
- [Documentation portal contract](../../technical/documentation-portal.md)
