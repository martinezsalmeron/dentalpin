---
module: verifactu
screen: queue
route: /settings/verifactu/queue
related_endpoints:
  - DELETE /api/v1/verifactu/certificate/{cert_id}
  - DELETE /api/v1/verifactu/producer/declaracion
  - GET /api/v1/verifactu/certificate
  - GET /api/v1/verifactu/certificate/history
  - GET /api/v1/verifactu/health
  - GET /api/v1/verifactu/nif-check
  - GET /api/v1/verifactu/producer/defaults
  - GET /api/v1/verifactu/queue
  - GET /api/v1/verifactu/records
  - GET /api/v1/verifactu/records/{record_id}
  - GET /api/v1/verifactu/records/{record_id}/attempts
  - GET /api/v1/verifactu/records/{record_id}/xml
  - GET /api/v1/verifactu/settings
  - GET /api/v1/verifactu/vat-mapping
  - POST /api/v1/verifactu/certificate
  - POST /api/v1/verifactu/queue/process-now
  - POST /api/v1/verifactu/queue/retry-all
  - POST /api/v1/verifactu/queue/{record_id}/retry
  - PUT /api/v1/verifactu/producer
  - PUT /api/v1/verifactu/settings
  - PUT /api/v1/verifactu/vat-mapping/{vat_type_id}
related_permissions:
  - verifactu.settings.read
  - verifactu.settings.configure
  - verifactu.records.read
  - verifactu.queue.manage
  - verifactu.environment.promote
related_paths:
  - backend/app/modules/verifactu/frontend/pages/settings/verifactu/queue.vue
last_verified_commit: 0000000
---

# /settings/verifactu/queue

> _Esqueleto generado automáticamente — reemplazar con documentación real cuando se toque este módulo._

_Pantalla `/settings/verifactu/queue` del módulo `verifactu`._

## Permisos

- `verifactu.settings.read`
- `verifactu.settings.configure`
- `verifactu.records.read`
- `verifactu.queue.manage`
- `verifactu.environment.promote`

## Para qué sirve

_Pendiente de documentar._

