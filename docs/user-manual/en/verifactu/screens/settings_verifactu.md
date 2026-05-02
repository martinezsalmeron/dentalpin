---
module: verifactu
screen: verifactu
route: /settings/verifactu
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
  - backend/app/modules/verifactu/frontend/pages/settings/verifactu/index.vue
last_verified_commit: 0000000
---

# /settings/verifactu

> _Scaffolded stub — replace with proper documentation when this module is next touched._

_Screen `/settings/verifactu` of the `verifactu` module._

## Permissions

- `verifactu.settings.read`
- `verifactu.settings.configure`
- `verifactu.records.read`
- `verifactu.queue.manage`
- `verifactu.environment.promote`

## What this screen does

_Documentation pending._

