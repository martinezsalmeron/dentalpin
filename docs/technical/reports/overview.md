---
module: reports
last_verified_commit: 0000000
---

# Reports — technical overview

> _Scaffolded stub — replace with proper documentation when this module is next touched._

Auto-discovered facts about the `reports` module. See the module's
own notes at `backend/app/modules/reports/CLAUDE.md` for context
the scaffold could not infer.

## API surface

- `GET /api/v1/reports/billing/by-payment-method`
- `GET /api/v1/reports/billing/by-professional`
- `GET /api/v1/reports/billing/gaps`
- `GET /api/v1/reports/billing/overdue`
- `GET /api/v1/reports/billing/summary`
- `GET /api/v1/reports/billing/vat-summary`
- `GET /api/v1/reports/budgets/by-professional`
- `GET /api/v1/reports/budgets/by-status`
- `GET /api/v1/reports/budgets/by-treatment`
- `GET /api/v1/reports/budgets/summary`
- `GET /api/v1/reports/scheduling/by-cabinet`
- `GET /api/v1/reports/scheduling/by-day-of-week`
- `GET /api/v1/reports/scheduling/by-professional`
- `GET /api/v1/reports/scheduling/duration-variance`
- `GET /api/v1/reports/scheduling/first-visits`
- `GET /api/v1/reports/scheduling/funnel`
- `GET /api/v1/reports/scheduling/punctuality`
- `GET /api/v1/reports/scheduling/summary`
- `GET /api/v1/reports/scheduling/waiting-times`

## Frontend

- `backend/app/modules/reports/frontend/pages/reports/index.vue` → `/reports`
- `backend/app/modules/reports/frontend/pages/reports/billing.vue` → `/reports/billing`
- `backend/app/modules/reports/frontend/pages/reports/budgets.vue` → `/reports/budgets`
- `backend/app/modules/reports/frontend/pages/reports/scheduling.vue` → `/reports/scheduling`

## Permissions

`billing.read`, `budgets.read`, `scheduling.read`

See [`./permissions.md`](./permissions.md) for the full role mapping.

## Events

- **Emits:** _(none)_
- **Subscribes:** _(none)_

module participates in the event bus).

## See also

- Module CLAUDE notes: `backend/app/modules/reports/CLAUDE.md`
- [Documentation portal contract](../../technical/documentation-portal.md)
