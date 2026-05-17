---
module: migration_import
last_verified_commit: HEAD
locale: en
screen: data-migration
path: /settings/workspace/data-migration
related_endpoints:
  - POST /api/v1/migration-import/jobs
  - POST /api/v1/migration-import/jobs/{id}/validate
  - POST /api/v1/migration-import/jobs/{id}/preview
  - POST /api/v1/migration-import/jobs/{id}/execute
  - GET  /api/v1/migration-import/jobs/{id}
  - POST /api/v1/migration-import/jobs/{id}/binaries
permissions:
  - migration_import.job.read
  - migration_import.job.write
  - migration_import.job.execute
---

# Screen — Data migration

Single-page wizard located at **Settings → Workspace → Data migration**.

## Layout

| Section          | What it shows |
|------------------|---------------|
| **Upload card**  | File picker + passphrase input. Only visible until the first upload. |
| **Job header**   | Filename, source system, format version, file size, status badge. |
| **Preview list** | Entity counts (one row per DPMF entity type). |
| **Files summary**| Total binaries expected vs sha256-known. |
| **Warnings list**| Up to all warnings emitted by the extractor + this importer. |
| **Verifactu checkbox** | Visible only when Verifactu is installed AND the file contains legal hashes. |
| **Confirm button** | Triggers `POST /execute`. Gated by `migration_import.job.execute`. |
| **Progress**     | While `status = executing`, shows *X of Y entities*. Polls every 2 s. |

## Permissions

The page itself requires `migration_import.job.read`. The **Confirm**
button is disabled for any role without `migration_import.job.execute`.

## Screenshots

_(none yet — capture when first deployed)_
