---
module: migration_import
last_verified_commit: HEAD
---

# migration_import

Optional, installable/removable module that consumes a [DPMF v0.1](https://github.com/dentaltix/dental-bridge/blob/main/spec/dpmf-v0.1.md)
file produced by [dental-bridge](https://github.com/dentaltix/dental-bridge)
and hydrates the current clinic with the extracted data. Issue #78.

## Status

- **Installable**: yes
- **Auto-install**: no (admin activates from the modules page)
- **Removable**: yes (own Alembic branch, uninstall round-trip green)
- **Depends**: `patients`, `schedules`, `treatment_plan`, `billing`,
  `payments`, `media`. `verifactu` is intentionally **not** in
  `depends` so PT/FR clinics can import without it.

## What it does

1. Operator uploads a `.dpm` file (raw / zstd / encrypted).
2. The module validates the file (magic bytes → decrypt → decompress →
   integrity hash → format version gate).
3. The operator reviews a preview (entity counts, sample rows,
   DPMF warnings, total binaries expected from `_files`).
4. The operator confirms; mappers run as a BackgroundTask and call
   each target module's service.
5. The external sync agent (lives in dental-bridge) uploads each
   binary one by one against `POST /jobs/{id}/binaries`; matched by
   sha256 they land in `media` storage with full thumbnails / MIME
   validation.

## Architecture highlights

- **Idempotent**: every persisted DentalPin row gets an
  `entity_mappings` row keyed by
  `(clinic_id, source_system, canonical_uuid, entity_type)`.
  Re-running a job is a no-op.
- **`verifactu` opt-in at runtime**: the fiscal-document mapper
  detects the module at runtime via `module_registry.is_loaded(...)`.
  Legal hashes (Hash / HashControl / ATCUD / QR) are preserved only
  when (a) verifactu is loaded AND (b) the operator ticked
  *"Importar datos legales Verifactu"* in the preview.
- **Mapper coverage today**: `patient`, `professional`,
  `patient_document`, `payment`, `fiscal_document`. Everything else
  lands in `raw_entities` for forward-compatibility — a future module
  rehydrates from there without re-importing.
- **Multi-tenant safe**: every query filters `clinic_id`. The
  importer never trusts the `clinic_id`/`tenant_label` recorded in
  the DPMF — `ctx.clinic_id` wins.
- **No rollback in v1**: documented in the UI. Admin restores from
  backup if a partial import is unrecoverable.

## See also

- Module CLAUDE: `backend/app/modules/migration_import/CLAUDE.md`
- Technical overview: `docs/technical/migration_import/overview.md`
- Events: `docs/technical/migration_import/events.md`
- Permissions: `docs/technical/migration_import/permissions.md`
- User manual (ES/EN): `docs/user-manual/{en,es}/migration_import/`
