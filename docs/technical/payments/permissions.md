---
module: payments
last_verified_commit: 0000000
---

# Payments — permissions

> _Scaffolded stub — replace with proper documentation when this module is next touched._

Returned by `PaymentsModule.get_permissions()`
(relative names; the registry namespaces them as `payments.<name>`).

| Permission | Allows | Required by |
|------------|--------|-------------|
| `payments.record.read` | _Describe what this allows._ | _List the endpoints._ |
| `payments.record.write` | _Describe what this allows._ | _List the endpoints._ |
| `payments.record.refund` | _Describe what this allows._ | _List the endpoints._ |
| `payments.reports.read` | _Describe what this allows._ | _List the endpoints._ |

## Role assignment

See `backend/app/core/auth/permissions.py` for the canonical role table.

## Adding a new permission

1. Add the relative name to `get_permissions()` in
   `backend/app/modules/payments/__init__.py` (or `module.py`).
2. Add the namespaced form to the relevant role(s) in
   `backend/app/core/auth/permissions.py`.
3. Add a row to the table above.
4. Annotate the endpoint(s) with `Depends(require_permission(...))`.
5. Update `frontend/app/config/permissions.ts` if it gates UI.
