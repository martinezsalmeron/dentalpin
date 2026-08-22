---
module: india_gst
last_verified_commit: 0000000
---

# India GST — technical overview

> _Scaffolded stub — replace with proper documentation when this module is next touched._

Auto-discovered facts about the `india_gst` module. See the module's
own notes at `backend/app/modules/india_gst/CLAUDE.md` for context
the scaffold could not infer.

## API surface

- `GET /api/v1/india_gst/catalog-defaults`
- `GET /api/v1/india_gst/invoices/{invoice_id}/einvoice`
- `GET /api/v1/india_gst/reports/export`
- `GET /api/v1/india_gst/reports/summary`
- `GET /api/v1/india_gst/reports/transactions`
- `GET /api/v1/india_gst/settings`
- `POST /api/v1/india_gst/invoices/{invoice_id}/einvoice/retry`
- `POST /api/v1/india_gst/tax-preview`
- `PUT /api/v1/india_gst/catalog-defaults/{catalog_item_id}`
- `PUT /api/v1/india_gst/invoices/{invoice_id}`
- `PUT /api/v1/india_gst/settings`

## Frontend

- `backend/app/modules/india_gst/frontend/pages/settings/india-gst/index.vue` → `/settings/india-gst`
- `backend/app/modules/india_gst/frontend/pages/reports/india-gst.vue` → `/reports/india-gst`

## Permissions

`settings.read`, `settings.configure`, `catalog.manage`, `reports.read`

See [`./permissions.md`](./permissions.md) for the full role mapping.

## Events

- **Emits:** _(none)_
- **Subscribes:** _(none)_

See [`./events.md`](./events.md) for the per-event detail (when the
module participates in the event bus).

## See also

- Module CLAUDE notes: `backend/app/modules/india_gst/CLAUDE.md`
- [Documentation portal contract](../../technical/documentation-portal.md)
