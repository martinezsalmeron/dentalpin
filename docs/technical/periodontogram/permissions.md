---
module: periodontogram
last_verified_commit: 452a17e
---

# Periodontogram — permissions

Returned by `PeriodontogramModule.get_permissions()`
(relative names; the registry namespaces them as `periodontogram.<name>`).

| Permission | Allows | Required by |
|------------|--------|-------------|
| `periodontogram.read` | List snapshots, fetch drafts / closed snapshots, read computed indices. | `GET /patients/{id}/snapshots`, `GET /patients/{id}/timeline`, `GET /patients/{id}/draft`, `GET /snapshots/{id}`, `GET /snapshots/{id}/indices` |
| `periodontogram.write` | Create drafts, edit per-tooth / per-site fields, close drafts (compute indices), delete drafts. | `POST /patients/{id}/draft`, `PATCH /snapshots/{id}/teeth/{tn}`, `PATCH /snapshots/{id}/teeth/{tn}/sites/{site}`, `POST /snapshots/{id}/close`, `DELETE /snapshots/{id}` |

## Role assignment

Default `role_permissions` in the module manifest grants `*` (both
permissions) to `admin` and `dentist`. See
`backend/app/core/auth/permissions.py` for the canonical role table.

## Adding a new permission

1. Add the relative name to `get_permissions()` in
   `backend/app/modules/periodontogram/__init__.py`.
2. List it under `manifest.role_permissions`.
3. Add a row to the table above.
4. Annotate the endpoint(s) with `Depends(require_permission(...))`.
5. Update `frontend/app/config/permissions.ts` if it gates UI.
