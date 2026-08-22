---
module: india_gst
screen: india_gst_settings
route: /settings/india-gst
related_endpoints:
  - GET /api/v1/india_gst/settings
  - PUT /api/v1/india_gst/settings
  - GET /api/v1/india_gst/catalog-defaults
  - PUT /api/v1/india_gst/catalog-defaults/{catalog_item_id}
related_permissions:
  - india_gst.settings.read
  - india_gst.settings.configure
  - india_gst.catalog.manage
related_paths:
  - backend/app/modules/india_gst/frontend/pages/settings/india-gst/index.vue
last_verified_commit: d158c2f
---

# /settings/india-gst

> _Borrador generado automáticamente — sustituir por documentación completa la próxima vez que se toque este módulo._

_Pantalla `/settings/india-gst` del módulo `india_gst`._

## Permisos

- `india_gst.settings.read`
- `india_gst.settings.configure`
- `india_gst.catalog.manage`
