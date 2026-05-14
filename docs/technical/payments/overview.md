---
module: payments
last_verified_commit: 0000000
---

# Payments — technical overview

> _Scaffolded stub — replace with proper documentation when this module is next touched._

Auto-discovered facts about the `payments` module. See the module's
own notes at `backend/app/modules/payments/CLAUDE.md` for context
the scaffold could not infer.

## API surface

- `GET /api/v1/payments`
- `GET /api/v1/payments/budgets/{budget_id}/allocations`
- `GET /api/v1/payments/filters/budgets-by-status`
- `GET /api/v1/payments/filters/patients-with-debt`
- `GET /api/v1/payments/patients/{patient_id}/ledger`
- `GET /api/v1/payments/reports/aging-receivables`
- `GET /api/v1/payments/reports/by-method`
- `GET /api/v1/payments/reports/by-professional`
- `GET /api/v1/payments/reports/refunds`
- `GET /api/v1/payments/reports/summary`
- `GET /api/v1/payments/reports/trends`
- `GET /api/v1/payments/{payment_id}`
- `GET /api/v1/payments/{payment_id}/refunds`
- `POST /api/v1/payments`
- `POST /api/v1/payments/summary/by-budgets`
- `POST /api/v1/payments/summary/by-patients`
- `POST /api/v1/payments/{payment_id}/reallocate`
- `POST /api/v1/payments/{payment_id}/refunds`

## Frontend

- `backend/app/modules/payments/frontend/pages/payments/index.vue` → `/payments`
- `backend/app/modules/payments/frontend/pages/reports/payments/index.vue` → `/reports/payments`

## Permissions

`record.read`, `record.write`, `record.refund`, `reports.read`
See [`./permissions.md`](./permissions.md) for the full role mapping.

## Events

- **Emits:** _(none)_
- **Subscribes:** `odontogram.treatment.performed`, `treatment_plan.treatment_completed`

See [`./events.md`](./events.md) for the per-event detail.

## See also

- Module CLAUDE notes: `backend/app/modules/payments/CLAUDE.md`
- [Documentation portal contract](../../technical/documentation-portal.md)
