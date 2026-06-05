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

> _Esqueleto generado automáticamente — reemplazar con documentación real cuando se toque este módulo._

_Pantalla `/copilot` del módulo `copilot`._

## Permisos

- `copilot.chat`
- `copilot.history.read`
- `copilot.history.read_all`
- `copilot.supervise`
- `copilot.configure`

## Para qué sirve

_Pendiente de documentar._

