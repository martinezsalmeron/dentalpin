---
module: odontogram
last_verified_commit: 0000000
---

# Odontogram — technical overview

> _Scaffolded stub — replace with proper documentation when this module is next touched._

Auto-discovered facts about the `odontogram` module. See the module's
own notes at `backend/app/modules/odontogram/CLAUDE.md` for context
the scaffold could not infer.

## API surface

- `DELETE /api/v1/odontogram/treatments/{treatment_id}`
- `GET /api/v1/odontogram/patients/{patient_id}/history`
- `GET /api/v1/odontogram/patients/{patient_id}/odontogram`
- `GET /api/v1/odontogram/patients/{patient_id}/odontogram/at`
- `GET /api/v1/odontogram/patients/{patient_id}/odontogram/timeline`
- `GET /api/v1/odontogram/patients/{patient_id}/teeth/{tooth_number}`
- `GET /api/v1/odontogram/patients/{patient_id}/teeth/{tooth_number}/full`
- `GET /api/v1/odontogram/patients/{patient_id}/teeth/{tooth_number}/history`
- `GET /api/v1/odontogram/patients/{patient_id}/treatments`
- `GET /api/v1/odontogram/treatments/{treatment_id}`
- `PATCH /api/v1/odontogram/patients/{patient_id}/teeth/bulk`
- `PATCH /api/v1/odontogram/patients/{patient_id}/teeth/{tooth_number}`
- `PATCH /api/v1/odontogram/treatments/{treatment_id}/perform`
- `POST /api/v1/odontogram/patients/{patient_id}/treatments`
- `PUT /api/v1/odontogram/patients/{patient_id}/teeth/{tooth_number}`
- `PUT /api/v1/odontogram/treatments/{treatment_id}`

## Frontend

_This module ships no Nuxt pages._

## Permissions

`read`, `write`, `treatments.read`, `treatments.write`

See [`./permissions.md`](./permissions.md) for the full role mapping.

## Events

- **Emits:** _(none)_
- **Subscribes:** _(none)_

module participates in the event bus).

## See also

- Module CLAUDE notes: `backend/app/modules/odontogram/CLAUDE.md`
- [Documentation portal contract](../../technical/documentation-portal.md)
