---
module: copilot
last_verified_commit: 0000000
---

# Copilot — permissions

Returned by `CopilotModule.get_permissions()`
(relative names; the registry namespaces them as `copilot.<name>`).

| Permission | Allows | Required by |
|------------|--------|-------------|
| `copilot.chat` | Start/continue a chat session, confirm pending writes, and read the Pendientes feed + nudges. | `POST /sessions`, `POST /sessions/{id}/messages`, `POST /sessions/{id}/confirmations/{cid}`, `POST /sessions/{id}/end`, `GET /pending`, `GET /nudges`, `POST /nudges/{id}/dismiss` |
| `copilot.history.read` | Replay one's own conversations. | `GET /sessions`, `GET /sessions/{id}/messages` |
| `copilot.history.read_all` | List/replay other users' conversations (supervisor view). | `GET /sessions` (cross-user) |
| `copilot.supervise` | Read usage observability (tool-call counts, error rate, latency, token budget). | `GET /metrics` |
| `copilot.configure` | Read/update per-clinic provider, budget and digest settings. | `GET /settings`, `PATCH /settings` |

## Role assignment

See `backend/app/core/auth/permissions.py` for the canonical role table.

## Adding a new permission

1. Add the relative name to `get_permissions()` in
   `backend/app/modules/copilot/__init__.py` (or `module.py`).
2. Add the namespaced form to the relevant role(s) in
   `backend/app/core/auth/permissions.py`.
3. Add a row to the table above.
4. Annotate the endpoint(s) with `Depends(require_permission(...))`.
5. Update `frontend/app/config/permissions.ts` if it gates UI.
