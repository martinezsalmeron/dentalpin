---
module: reports
screen: budgets
route: /reports/budgets
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
  - backend/app/modules/reports/frontend/pages/reports/budgets.vue
last_verified_commit: 0000000
---

# /reports/budgets

> _Esqueleto generado automáticamente — reemplazar con documentación real cuando se toque este módulo._

_Pantalla `/reports/budgets` del módulo `reports`._

## Permisos

- `reports.billing.read`
- `reports.budgets.read`
- `reports.scheduling.read`

## Para qué sirve

_Pendiente de documentar._

