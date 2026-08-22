---
module: expenses
screen: index
route: /expenses
related_endpoints:
  - GET /api/v1/expenses
  - GET /api/v1/expenses/monthly-totals
  - POST /api/v1/expenses
  - PATCH /api/v1/expenses/{expense_id}
  - DELETE /api/v1/expenses/{expense_id}
related_permissions:
  - expenses.read
  - expenses.write
related_paths:
  - backend/app/modules/expenses/frontend/pages/expenses/index.vue
last_verified_commit: 0000000
---

# /expenses

Fixed and recurring office cost tracking — rent, utilities, salaries,
supplies, equipment, insurance, maintenance, and other.

## Permissions

- `expenses.read` — view the list (`admin` plus every other role by
  default).
- `expenses.write` — add, edit, delete (`admin` only by default).

## What this screen does

- **Filter** the list by category and date range.
- **Add expense** — opens a modal for category, amount, date, and an
  optional description.
- **Edit / delete** per row, gated behind `expenses.write`.
