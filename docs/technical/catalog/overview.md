---
module: catalog
last_verified_commit: 0000000
---

# Catalog — technical overview

> _Scaffolded stub — replace with proper documentation when this module is next touched._

Auto-discovered facts about the `catalog` module. See the module's
own notes at `backend/app/modules/catalog/CLAUDE.md` for context
the scaffold could not infer.

## API surface

- `DELETE /api/v1/catalog/categories/{category_id}`
- `DELETE /api/v1/catalog/items/{item_id}`
- `DELETE /api/v1/catalog/vat-types/{vat_type_id}`
- `GET /api/v1/catalog/categories`
- `GET /api/v1/catalog/categories/{category_id}`
- `GET /api/v1/catalog/items`
- `GET /api/v1/catalog/items/popular`
- `GET /api/v1/catalog/items/search`
- `GET /api/v1/catalog/items/{item_id}`
- `GET /api/v1/catalog/odontogram-treatments`
- `GET /api/v1/catalog/odontogram-treatments/by-category`
- `GET /api/v1/catalog/vat-types`
- `GET /api/v1/catalog/vat-types/default`
- `GET /api/v1/catalog/vat-types/{vat_type_id}`
- `POST /api/v1/catalog/categories`
- `POST /api/v1/catalog/items`
- `POST /api/v1/catalog/vat-types`
- `PUT /api/v1/catalog/categories/{category_id}`
- `PUT /api/v1/catalog/items/{item_id}`
- `PUT /api/v1/catalog/vat-types/{vat_type_id}`

## Frontend

- `backend/app/modules/catalog/frontend/pages/settings/catalog/index.vue` → `/settings/catalog`
- `backend/app/modules/catalog/frontend/pages/settings/vat-types/index.vue` → `/settings/vat-types`

## Permissions

`read`, `write`, `admin`

See [`./permissions.md`](./permissions.md) for the full role mapping.

## Events

- **Emits:** _(none)_
- **Subscribes:** _(none)_

module participates in the event bus).

## See also

- Module CLAUDE notes: `backend/app/modules/catalog/CLAUDE.md`
- [Documentation portal contract](../../technical/documentation-portal.md)
