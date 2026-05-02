---
module: billing
last_verified_commit: 0000000
---

# Billing — permissions

> _Scaffolded stub — replace with proper documentation when this module is next touched._

Returned by `BillingModule.get_permissions()`
(relative names; the registry namespaces them as `billing.<name>`).

| Permission | Allows | Required by |
|------------|--------|-------------|
| `billing.read` | _Describe what this allows._ | _List the endpoints._ |
| `billing.write` | _Describe what this allows._ | _List the endpoints._ |
| `billing.admin` | _Describe what this allows._ | _List the endpoints._ |

## Role assignment

See `backend/app/core/auth/permissions.py` for the canonical role table.

## Adding a new permission

1. Add the relative name to `get_permissions()` in
   `backend/app/modules/billing/__init__.py` (or `module.py`).
2. Add the namespaced form to the relevant role(s) in
   `backend/app/core/auth/permissions.py`.
3. Add a row to the table above.
4. Annotate the endpoint(s) with `Depends(require_permission(...))`.
5. Update `frontend/app/config/permissions.ts` if it gates UI.
