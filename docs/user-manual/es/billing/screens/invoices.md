---
module: billing
screen: list
route: /invoices
related_endpoints:
  - DELETE /api/v1/billing/invoices/{invoice_id}
  - DELETE /api/v1/billing/invoices/{invoice_id}/items/{item_id}
  - GET /api/v1/billing/invoices
  - GET /api/v1/billing/invoices/{invoice_id}
  - GET /api/v1/billing/invoices/{invoice_id}/history
  - GET /api/v1/billing/invoices/{invoice_id}/payments
  - GET /api/v1/billing/invoices/{invoice_id}/pdf
  - GET /api/v1/billing/invoices/{invoice_id}/pdf/preview
  - GET /api/v1/billing/patients/{patient_id}/summary
  - GET /api/v1/billing/series
  - GET /api/v1/billing/settings
  - PATCH /api/v1/billing/invoices/{invoice_id}/billing-party
  - POST /api/v1/billing/invoices
  - POST /api/v1/billing/invoices/from-budget/{budget_id}
  - POST /api/v1/billing/invoices/{invoice_id}/credit-note
  - POST /api/v1/billing/invoices/{invoice_id}/issue
  - POST /api/v1/billing/invoices/{invoice_id}/items
  - POST /api/v1/billing/invoices/{invoice_id}/payments
  - POST /api/v1/billing/invoices/{invoice_id}/send-email
  - POST /api/v1/billing/invoices/{invoice_id}/void
  - POST /api/v1/billing/payments/{payment_id}/void
  - POST /api/v1/billing/series
  - POST /api/v1/billing/series/{series_id}/reset
  - PUT /api/v1/billing/invoices/{invoice_id}
  - PUT /api/v1/billing/invoices/{invoice_id}/items/{item_id}
  - PUT /api/v1/billing/series/{series_id}
  - PUT /api/v1/billing/settings
related_permissions:
  - billing.read
  - billing.write
  - billing.admin
related_paths:
  - backend/app/modules/billing/frontend/pages/invoices/index.vue
last_verified_commit: 0000000
---

# /invoices

> _Esqueleto generado automáticamente — reemplazar con documentación real cuando se toque este módulo._

_Pantalla `/invoices` del módulo `billing`._

## Permisos

- `billing.read`
- `billing.write`
- `billing.admin`

## Para qué sirve

_Pendiente de documentar._

