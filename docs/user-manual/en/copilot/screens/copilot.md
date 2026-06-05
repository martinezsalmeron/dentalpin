---
module: copilot
screen: list
route: /copilot
related_endpoints:
  - GET /api/v1/copilot/sessions
  - GET /api/v1/copilot/sessions/{conversation_id}/messages
  - GET /api/v1/copilot/settings
  - PATCH /api/v1/copilot/settings
  - POST /api/v1/copilot/sessions
  - POST /api/v1/copilot/sessions/{conversation_id}/confirmations/{call_id}
  - POST /api/v1/copilot/sessions/{conversation_id}/end
  - POST /api/v1/copilot/sessions/{conversation_id}/messages
related_permissions:
  - copilot.chat
  - copilot.history.read
  - copilot.history.read_all
  - copilot.supervise
  - copilot.configure
related_paths:
  - backend/app/modules/copilot/frontend/pages/copilot/index.vue
last_verified_commit: 0000000
---

# /copilot

> _Scaffolded stub — replace with proper documentation when this module is next touched._

_Screen `/copilot` of the `copilot` module._

## Permissions

- `copilot.chat`
- `copilot.history.read`
- `copilot.history.read_all`
- `copilot.supervise`
- `copilot.configure`

## What this screen does

_Documentation pending._

