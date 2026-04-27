# Media module

Patient documents, images, file storage abstraction.

## Public API

Routes mounted at `/api/v1/media/`. Upload, download, delete,
list-by-patient.

## Dependencies

`manifest.depends = ["patients"]`.

## Permissions

`media.documents.read`, `media.documents.write`.

## Events emitted

- `document.uploaded`
- `document.deleted`

## Events consumed

- `patient.archived` → archive associated documents (soft).

## Lifecycle

- `removable=False`. Treatment_plan, patient_timeline depend on
  documents.

## Gotchas

- **Storage backend is pluggable** (`STORAGE_BACKEND` env var).
  Currently `local`; future backends must implement the same interface.
- **MIME validation is mandatory** — see `validation.py`. Don't bypass
  on the upload path.
- **Files must be scoped by `clinic_id`** in the storage layout to
  prevent cross-tenant access bugs.

## Related ADRs

- `docs/adr/0001-modular-plugin-architecture.md`
- `docs/adr/0003-event-bus-over-direct-imports.md`

## CHANGELOG

See `./CHANGELOG.md`.
