---
module: budget
last_verified_commit: 0000000
---

# Budget — permissions

> _Scaffolded stub — replace with proper documentation when this module is next touched._

Returned by `BudgetModule.get_permissions()`
(relative names; the registry namespaces them as `budget.<name>`).

| Permission | Allows | Required by |
|------------|--------|-------------|
| `budget.read` | _Describe what this allows._ | _List the endpoints._ |
| `budget.write` | _Describe what this allows._ | _List the endpoints._ |
| `budget.admin` | _Describe what this allows._ | _List the endpoints._ |
| `budget.renegotiate` | _Describe what this allows._ | _List the endpoints._ |
| `budget.accept_in_clinic` | _Describe what this allows._ | _List the endpoints._ |

## Role assignment

See `backend/app/core/auth/permissions.py` for the canonical role table.

## Adding a new permission

1. Add the relative name to `get_permissions()` in
   `backend/app/modules/budget/__init__.py` (or `module.py`).
2. Add the namespaced form to the relevant role(s) in
   `backend/app/core/auth/permissions.py`.
3. Add a row to the table above.
4. Annotate the endpoint(s) with `Depends(require_permission(...))`.
5. Update `frontend/app/config/permissions.ts` if it gates UI.
