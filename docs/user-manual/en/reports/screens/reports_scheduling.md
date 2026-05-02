---
module: reports
screen: scheduling
route: /reports/scheduling
related_endpoints:
  - GET /api/v1/reports/billing/by-payment-method
  - GET /api/v1/reports/billing/by-professional
  - GET /api/v1/reports/billing/gaps
  - GET /api/v1/reports/billing/overdue
  - GET /api/v1/reports/billing/summary
  - GET /api/v1/reports/billing/vat-summary
  - GET /api/v1/reports/budgets/by-professional
  - GET /api/v1/reports/budgets/by-status
  - GET /api/v1/reports/budgets/by-treatment
  - GET /api/v1/reports/budgets/summary
  - GET /api/v1/reports/scheduling/by-cabinet
  - GET /api/v1/reports/scheduling/by-day-of-week
  - GET /api/v1/reports/scheduling/by-professional
  - GET /api/v1/reports/scheduling/duration-variance
  - GET /api/v1/reports/scheduling/first-visits
  - GET /api/v1/reports/scheduling/funnel
  - GET /api/v1/reports/scheduling/punctuality
  - GET /api/v1/reports/scheduling/summary
  - GET /api/v1/reports/scheduling/waiting-times
related_permissions:
  - reports.billing.read
  - reports.budgets.read
  - reports.scheduling.read
related_paths:
  - backend/app/modules/reports/frontend/pages/reports/scheduling.vue
last_verified_commit: 0000000
---

# /reports/scheduling

> _Scaffolded stub — replace with proper documentation when this module is next touched._

_Screen `/reports/scheduling` of the `reports` module._

## Permissions

- `reports.billing.read`
- `reports.budgets.read`
- `reports.scheduling.read`

## What this screen does

_Documentation pending._

