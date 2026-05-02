---
module: recalls
screen: list
route: /recalls
related_endpoints:
  - DELETE /api/v1/recalls/{recall_id}
  - GET /api/v1/recalls
  - GET /api/v1/recalls/export.csv
  - GET /api/v1/recalls/patients/{patient_id}
  - GET /api/v1/recalls/settings
  - GET /api/v1/recalls/stats/dashboard
  - GET /api/v1/recalls/suggestions/next
  - GET /api/v1/recalls/{recall_id}
  - GET /api/v1/recalls/{recall_id}/attempts
  - PATCH /api/v1/recalls/{recall_id}
  - POST /api/v1/recalls
  - POST /api/v1/recalls/{recall_id}/attempts
  - POST /api/v1/recalls/{recall_id}/cancel
  - POST /api/v1/recalls/{recall_id}/done
  - POST /api/v1/recalls/{recall_id}/link-appointment
  - POST /api/v1/recalls/{recall_id}/snooze
  - PUT /api/v1/recalls/settings
related_permissions:
  - recalls.read
  - recalls.write
  - recalls.delete
related_paths:
  - backend/app/modules/recalls/frontend/pages/recalls/index.vue
last_verified_commit: 0000000
---

# /recalls

> _Scaffolded stub — replace with proper documentation when this module is next touched._

_Screen `/recalls` of the `recalls` module._

## Permissions

- `recalls.read`
- `recalls.write`
- `recalls.delete`

## What this screen does

_Documentation pending._

