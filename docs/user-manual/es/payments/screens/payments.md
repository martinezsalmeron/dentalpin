---
module: payments
screen: list
route: /payments
related_endpoints:
  - GET /api/v1/payments
  - GET /api/v1/payments/budgets/{budget_id}/allocations
  - GET /api/v1/payments/filters/budgets-by-status
  - GET /api/v1/payments/filters/patients-with-debt
  - GET /api/v1/payments/patients/{patient_id}/ledger
  - GET /api/v1/payments/reports/aging-receivables
  - GET /api/v1/payments/reports/by-method
  - GET /api/v1/payments/reports/by-professional
  - GET /api/v1/payments/reports/refunds
  - GET /api/v1/payments/reports/summary
  - GET /api/v1/payments/reports/trends
  - GET /api/v1/payments/{payment_id}
  - GET /api/v1/payments/{payment_id}/refunds
  - POST /api/v1/payments
  - POST /api/v1/payments/summary/by-budgets
  - POST /api/v1/payments/summary/by-patients
  - POST /api/v1/payments/{payment_id}/reallocate
  - POST /api/v1/payments/{payment_id}/refunds
related_permissions:
  - payments.record.read
  - payments.record.write
  - payments.record.refund
  - payments.reports.read
related_paths:
  - backend/app/modules/payments/frontend/pages/payments/index.vue
last_verified_commit: 0000000
---

# /payments

> _Esqueleto generado automáticamente — reemplazar con documentación real cuando se toque este módulo._

_Pantalla `/payments` del módulo `payments`._

## Permisos

- `payments.record.read`
- `payments.record.write`
- `payments.record.refund`
- `payments.reports.read`

## Para qué sirve

_Pendiente de documentar._

