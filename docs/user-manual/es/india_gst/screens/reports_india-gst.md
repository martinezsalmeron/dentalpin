---
module: india_gst
screen: india_gst_reports
route: /reports/india-gst
related_endpoints:
  - GET /api/v1/india_gst/reports/summary
  - GET /api/v1/india_gst/reports/transactions
  - GET /api/v1/india_gst/reports/export
related_permissions:
  - india_gst.reports.read
related_paths:
  - backend/app/modules/india_gst/frontend/pages/reports/india-gst.vue
last_verified_commit: d158c2f
---

# /reports/india-gst

> _Borrador generado automáticamente — sustituir por documentación completa la próxima vez que se toque este módulo._

_Pantalla `/reports/india-gst` del módulo `india_gst`. Informe de
transacciones/conciliación GST — no es un artefacto de presentación
GSTR-1 estatutario validado._

## Permisos

- `india_gst.reports.read`
