---
module: expenses
last_verified_commit: 0000000
---

# expenses — permissions

Namespaced by the registry from the module's `get_permissions()`.

| Permission | Gates | Endpoints |
|------------|-------|-----------|
| `expenses.read` | List, view, monthly totals | `GET /api/v1/expenses`, `GET /api/v1/expenses/monthly-totals` |
| `expenses.write` | Create, update, delete | `POST /api/v1/expenses`, `PATCH /api/v1/expenses/{id}`, `DELETE /api/v1/expenses/{id}` |

Default role mapping: `admin` has both; `dentist`, `hygienist`,
`assistant`, `receptionist` are read-only
(`role_permissions = {"admin": ["*"], "dentist": ["read"], "hygienist":
["read"], "assistant": ["read"], "receptionist": ["read"]}`).
