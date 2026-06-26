---
module: whatsapp_kapso
last_verified_commit: 0000000
---

# whatsapp_kapso — permissions

Namespaced by the registry from the module's `get_permissions()`.

| Permission | Gates | Endpoints |
|------------|-------|-----------|
| `whatsapp_kapso.settings.read` | View connection status | `GET /api/v1/whatsapp_kapso/settings` |
| `whatsapp_kapso.settings.write` | Manage credentials, sync + map templates, test send | `PUT /settings`, `POST /templates/sync`, `POST /templates/map`, `POST /test` |

Default role mapping: **admin only** (`role_permissions = {"admin": ["*"]}`).

## Public endpoint (no permission)

`POST /api/v1/whatsapp_kapso/webhook` is unauthenticated by design (vendor
callback). It is protected by a per-clinic HMAC signature
(`X-Webhook-Signature`) and clinic resolution via `phone_number_id`, plus a
rate limit. Never trust a `clinic_id` in the payload.
