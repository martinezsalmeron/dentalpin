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

> _Esqueleto generado automáticamente — reemplazar con documentación real cuando se toque este módulo._

_Pantalla `/budgets/[id]` del módulo `budget`._

## Permisos

- `budget.read`
- `budget.write`
- `budget.admin`
- `budget.renegotiate`
- `budget.accept_in_clinic`

## Para qué sirve

_Pendiente de documentar._

## Layout del sidebar

La columna derecha apila (de arriba a abajo):

1. **Tarjeta de cobros** (montada vía el slot `budget.detail.sidebar`
   desde el módulo `payments`): resumen compacto `Cobrado / Total` con
   barra de progreso, estado de pendiente en una sola línea e
   historial de cobros con icono de método y fecha relativa. El CTA
   "Cobrar" vive en el header de la tarjeta y se oculta cuando el
   presupuesto está saldado.
2. **Tarjeta de totales**: subtotal, descuento, IVA y total.
3. **Tarjeta de info**: número de presupuesto, versión, creador, fecha
   y plan de tratamiento asociado.

