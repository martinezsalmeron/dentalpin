---
module: clinical_notes
last_verified_commit: 0000000
---

# Clinical Notes — technical overview

> _Scaffolded stub — replace with proper documentation when this module is next touched._

Auto-discovered facts about the `clinical_notes` module. See the module's
own notes at `backend/app/modules/clinical_notes/CLAUDE.md` for context
the scaffold could not infer.

## API surface

- `DELETE /api/v1/clinical_notes/notes/{note_id}`
- `GET /api/v1/clinical_notes/attachments`
- `GET /api/v1/clinical_notes/note-templates`
- `GET /api/v1/clinical_notes/notes`
- `GET /api/v1/clinical_notes/patients/{patient_id}/by-plan`
- `GET /api/v1/clinical_notes/patients/{patient_id}/recent`
- `GET /api/v1/clinical_notes/treatment-plans/{plan_id}/merged`
- `PATCH /api/v1/clinical_notes/notes/{note_id}`
- `POST /api/v1/clinical_notes/notes`

## Frontend

_This module ships no Nuxt pages._

## Permissions

`notes.read`, `notes.write`

See [`./permissions.md`](./permissions.md) for the full role mapping.

## Events

- **Emits:** _(none)_
- **Subscribes:** _(none)_

module participates in the event bus).

## See also

- Module CLAUDE notes: `backend/app/modules/clinical_notes/CLAUDE.md`
- [Documentation portal contract](../../technical/documentation-portal.md)
