# migration_import module

DPMF importer. Optional, installable/removable. Issue #78.

Reads a `.dpm` file produced by [dental-bridge](https://github.com/dentaltix/dental-bridge),
validates it (magic bytes + integrity hash + format version), and
hydrates the current clinic by calling each target module's service.

## Public API

Routes mounted at `/api/v1/migration-import/`.

- `POST   /jobs`                       — `migration_import.job.write`. Upload `.dpm`.
- `POST   /jobs/{id}/validate`         — `migration_import.job.write`. Decrypt/decompress/verify hash.
- `POST   /jobs/{id}/preview`          — `migration_import.job.read`. Entity counts + sample rows + verifactu detection.
- `POST   /jobs/{id}/execute`          — `migration_import.job.execute`. Runs mappers as a BackgroundTask.
- `GET    /jobs`                       — `migration_import.job.read`.
- `GET    /jobs/{id}`                  — `migration_import.job.read`.
- `GET    /jobs/{id}/warnings`         — `migration_import.job.read`.
- `POST   /jobs/{id}/binaries`         — `migration_import.binary.write`. Sync agent uploads a binary; matched by sha256.

## Dependencies

`manifest.depends = ["patients", "schedules", "treatment_plan", "billing", "payments", "media"]`.

**`verifactu` is intentionally NOT in `depends`.** Portuguese/French
clinics import without it. The fiscal-document mapper detects it at
runtime through `module_registry.is_loaded("verifactu")` and gates
legal-hash preservation behind an operator opt-in checkbox shown in
the preview step.

## Permissions

`migration_import.job.read`, `job.write`, `job.execute`, `binary.write`.

Default `role_permissions` grants `*` to `admin` only — operators must
be promoted to admin to run a migration.

## Events emitted

| Event | When | Payload |
|---|---|---|
| `migration.job.started`     | execute begins                 | `job_id`, `clinic_id` |
| `migration.job.completed`   | execute finishes successfully  | `job_id`, `clinic_id`, `total_entities`, `warnings_count` |
| `migration.job.failed`      | unhandled exception            | `job_id`, `clinic_id`, `error` |
| `migration.binary.resolved` | sync agent uploaded a matching binary | `job_id`, `staging_id`, `document_id` |

Plus every event the mapped service publishes naturally
(`patient.created`, `payment.recorded`, …).

## Events consumed

`migration.entity.persisted` — internal progress signal published by
mappers. Used to bump `ImportJob.processed_entities`.

## Lifecycle

- `installable=True`, `auto_install=False` (opt-in from admin UI),
  `removable=True`. Uninstall round-trip lives in
  `backend/tests/test_uninstall_roundtrip.py`.
- Imported rows survive uninstall — they belong to `patients`,
  `payments`, etc., not to us. We only drop our staging tables.

## Gotchas

- **`clinic_id` always comes from `ctx`**, never from the DPMF payload.
  Mappers that read `clinic_id` from the file are a tenancy bug.
- **External IDs are never used as FKs.** Every cross-entity reference
  goes through `MappingResolver`. The `EntityMapping` table is the
  only source of truth for "this canonical_uuid became this dentalpin
  UUID".
- **Idempotency is per `(clinic_id, source_system, canonical_uuid,
  entity_type)`.** Re-running execute on the same job is safe.
- **No rollback in v1.** If a job fails halfway, the partial state
  stays. Admin restores from backup if catastrophic. Document this in
  the UI.
- **The passphrase is never persisted.** Held in process memory only
  during validate/preview.
- **Binaries go through `media.DocumentService`** so the storage path,
  thumbnails, MIME validation and clinic-scoping are honoured.

## Related ADRs

- `docs/adr/0001-modular-plugin-architecture.md`
- `docs/adr/0002-per-module-alembic-branches.md`
- `docs/adr/0003-event-bus-over-direct-imports.md`

## CHANGELOG

See `./CHANGELOG.md`.
