---
module: catalog
screen: catalog
route: /settings/catalog
related_endpoints:
  - DELETE /api/v1/catalog/categories/{category_id}
  - DELETE /api/v1/catalog/items/{item_id}
  - DELETE /api/v1/catalog/vat-types/{vat_type_id}
  - GET /api/v1/catalog/categories
  - GET /api/v1/catalog/categories/{category_id}
  - GET /api/v1/catalog/items
  - GET /api/v1/catalog/items/popular
  - GET /api/v1/catalog/items/search
  - GET /api/v1/catalog/items/{item_id}
  - GET /api/v1/catalog/odontogram-treatments
  - GET /api/v1/catalog/odontogram-treatments/by-category
  - GET /api/v1/catalog/vat-types
  - GET /api/v1/catalog/vat-types/default
  - GET /api/v1/catalog/vat-types/{vat_type_id}
  - POST /api/v1/catalog/categories
  - POST /api/v1/catalog/items
  - POST /api/v1/catalog/vat-types
  - PUT /api/v1/catalog/categories/{category_id}
  - PUT /api/v1/catalog/items/{item_id}
  - PUT /api/v1/catalog/vat-types/{vat_type_id}
related_permissions:
  - catalog.read
  - catalog.write
  - catalog.admin
related_paths:
  - backend/app/modules/catalog/frontend/pages/settings/catalog/index.vue
last_verified_commit: 0000000
---

# /settings/catalog

> _Esqueleto generado automáticamente — reemplazar con documentación real cuando se toque este módulo._

_Pantalla `/settings/catalog` del módulo `catalog`._

## Permisos

- `catalog.read`
- `catalog.write`
- `catalog.admin`

## Para qué sirve

_Pendiente de documentar._

