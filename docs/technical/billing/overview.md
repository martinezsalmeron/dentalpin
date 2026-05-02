---
module: billing
last_verified_commit: 0000000
---

# Billing — technical overview

> _Scaffolded stub — replace with proper documentation when this module is next touched._

Auto-discovered facts about the `billing` module. See the module's
own notes at `backend/app/modules/billing/CLAUDE.md` for context
the scaffold could not infer.

## API surface

- `DELETE /api/v1/billing/invoices/{invoice_id}`
- `DELETE /api/v1/billing/invoices/{invoice_id}/items/{item_id}`
- `GET /api/v1/billing/invoices`
- `GET /api/v1/billing/invoices/{invoice_id}`
- `GET /api/v1/billing/invoices/{invoice_id}/history`
- `GET /api/v1/billing/invoices/{invoice_id}/payments`
- `GET /api/v1/billing/invoices/{invoice_id}/pdf`
- `GET /api/v1/billing/invoices/{invoice_id}/pdf/preview`
- `GET /api/v1/billing/patients/{patient_id}/summary`
- `GET /api/v1/billing/series`
- `GET /api/v1/billing/settings`
- `PATCH /api/v1/billing/invoices/{invoice_id}/billing-party`
- `POST /api/v1/billing/invoices`
- `POST /api/v1/billing/invoices/from-budget/{budget_id}`
- `POST /api/v1/billing/invoices/{invoice_id}/credit-note`
- `POST /api/v1/billing/invoices/{invoice_id}/issue`
- `POST /api/v1/billing/invoices/{invoice_id}/items`
- `POST /api/v1/billing/invoices/{invoice_id}/payments`
- `POST /api/v1/billing/invoices/{invoice_id}/send-email`
- `POST /api/v1/billing/invoices/{invoice_id}/void`
- `POST /api/v1/billing/payments/{payment_id}/void`
- `POST /api/v1/billing/series`
- `POST /api/v1/billing/series/{series_id}/reset`
- `PUT /api/v1/billing/invoices/{invoice_id}`
- `PUT /api/v1/billing/invoices/{invoice_id}/items/{item_id}`
- `PUT /api/v1/billing/series/{series_id}`
- `PUT /api/v1/billing/settings`

## Frontend

- `backend/app/modules/billing/frontend/pages/invoices/index.vue` → `/invoices`
- `backend/app/modules/billing/frontend/pages/invoices/[id]/index.vue` → `/invoices/[id]`
- `backend/app/modules/billing/frontend/pages/invoices/[id]/edit.vue` → `/invoices/[id]/edit`
- `backend/app/modules/billing/frontend/pages/invoices/from-budget/[budgetId].vue` → `/invoices/from-budget/[budgetId]`
- `backend/app/modules/billing/frontend/pages/invoices/new.vue` → `/invoices/new`
- `backend/app/modules/billing/frontend/pages/settings/invoice-series/index.vue` → `/settings/invoice-series`

## Permissions

`read`, `write`, `admin`

See [`./permissions.md`](./permissions.md) for the full role mapping.

## Events

- **Emits:** _(none)_
- **Subscribes:** _(none)_

module participates in the event bus).

## See also

- Module CLAUDE notes: `backend/app/modules/billing/CLAUDE.md`
- [Documentation portal contract](../../technical/documentation-portal.md)
