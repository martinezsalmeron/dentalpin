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

> _Scaffolded stub — replace with proper documentation when this module is next touched._

_Screen `/reports/india-gst` of the `india_gst` module. GST
transaction/reconciliation report — not a validated statutory GSTR-1
filing artifact._

## Permissions

- `india_gst.reports.read`
