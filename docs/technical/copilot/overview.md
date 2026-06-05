---
module: copilot
last_verified_commit: 0000000
---

# Copilot — technical overview

> _Scaffolded stub — replace with proper documentation when this module is next touched._

Auto-discovered facts about the `copilot` module. See the module's
own notes at `backend/app/modules/copilot/CLAUDE.md` for context
the scaffold could not infer.

## API surface

- `GET /api/v1/copilot/sessions`
- `GET /api/v1/copilot/sessions/{conversation_id}/messages`
- `GET /api/v1/copilot/settings`
- `PATCH /api/v1/copilot/settings`
- `POST /api/v1/copilot/sessions`
- `POST /api/v1/copilot/sessions/{conversation_id}/confirmations/{call_id}`
- `POST /api/v1/copilot/sessions/{conversation_id}/end`
- `POST /api/v1/copilot/sessions/{conversation_id}/messages`

## Frontend

_This module ships no Nuxt pages._

## Permissions

`chat`, `history.read`, `history.read_all`, `supervise`, `configure`
See [`./permissions.md`](./permissions.md) for the full role mapping.


## See also

- Module CLAUDE notes: `backend/app/modules/copilot/CLAUDE.md`
- [Documentation portal contract](../../technical/documentation-portal.md)
