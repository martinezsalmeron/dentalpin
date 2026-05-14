---
module: budget
screen: detail
route: /budgets/[id]
related_endpoints:
  - DELETE /api/v1/budget/budgets/{budget_id}
  - DELETE /api/v1/budget/budgets/{budget_id}/items/{item_id}
  - GET /api/v1/budget/budgets
  - GET /api/v1/budget/budgets/{budget_id}
  - GET /api/v1/budget/budgets/{budget_id}/history
  - GET /api/v1/budget/budgets/{budget_id}/pdf
  - GET /api/v1/budget/budgets/{budget_id}/pdf/preview
  - GET /api/v1/budget/budgets/{budget_id}/pdf/signed
  - GET /api/v1/budget/budgets/{budget_id}/signature
  - GET /api/v1/budget/budgets/{budget_id}/versions
  - POST /api/v1/budget/budgets
  - POST /api/v1/budget/budgets/{budget_id}/accept
  - POST /api/v1/budget/budgets/{budget_id}/accept-in-clinic
  - POST /api/v1/budget/budgets/{budget_id}/cancel
  - POST /api/v1/budget/budgets/{budget_id}/duplicate
  - POST /api/v1/budget/budgets/{budget_id}/items
  - POST /api/v1/budget/budgets/{budget_id}/reject
  - POST /api/v1/budget/budgets/{budget_id}/renegotiate
  - POST /api/v1/budget/budgets/{budget_id}/resend
  - POST /api/v1/budget/budgets/{budget_id}/send
  - POST /api/v1/budget/budgets/{budget_id}/send-reminder
  - POST /api/v1/budget/budgets/{budget_id}/set-public-code
  - POST /api/v1/budget/budgets/{budget_id}/unlock-public
  - PUT /api/v1/budget/budgets/{budget_id}
  - PUT /api/v1/budget/budgets/{budget_id}/items/{item_id}
related_permissions:
  - budget.read
  - budget.write
  - budget.admin
  - budget.renegotiate
  - budget.accept_in_clinic
related_paths:
  - backend/app/modules/budget/frontend/pages/budgets/[id].vue
last_verified_commit: 0ba0a4a
---

# /budgets/[id]

> _Scaffolded stub — replace with proper documentation when this module is next touched._

_Screen `/budgets/[id]` of the `budget` module._

## Permissions

- `budget.read`
- `budget.write`
- `budget.admin`
- `budget.renegotiate`
- `budget.accept_in_clinic`

## What this screen does

_Documentation pending._

## Sidebar layout

The right-hand sidebar stacks (top → bottom):

1. **Payments card** (mounted via the `budget.detail.sidebar` slot from
   the `payments` module): compact `Collected / Total` summary with a
   progress bar, a one-line pending status, and a list of payment
   allocations with method icon + relative date. The "Collect" CTA
   lives in the card header and is hidden once the budget is settled.
2. **Totals card**: subtotal, discount, tax, total.
3. **Info card**: budget number, version, creator, date, linked plan.

