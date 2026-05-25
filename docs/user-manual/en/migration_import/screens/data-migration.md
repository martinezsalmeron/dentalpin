---
module: migration_import
last_verified_commit: HEAD
locale: en
screen: data-migration
route: /settings/workspace/data-migration
related_endpoints:
  - POST /api/v1/migration_import/jobs
  - POST /api/v1/migration_import/jobs/{id}/validate
  - POST /api/v1/migration_import/jobs/{id}/preview
  - POST /api/v1/migration_import/jobs/{id}/proposals
  - GET  /api/v1/migration_import/jobs/{id}/proposals
  - PATCH /api/v1/migration_import/jobs/{id}/proposals/{canonical_uuid}
  - POST /api/v1/migration_import/jobs/{id}/proposals/bulk_accept
  - POST /api/v1/migration_import/jobs/{id}/execute
  - GET  /api/v1/migration_import/jobs/{id}
  - POST /api/v1/migration_import/jobs/{id}/binaries
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
| **Catalog mapping review** | Builds proposals for every Gesdén `Tratamientos` row (POST `/proposals`), shows a table with the automatic proposal (link / fuzzy + score / create new), and lets the operator accept, ignore or relink per row. "Accept all matches ≥ 0.9" shortcut for high-confidence bulk acceptance. |
| **Professional filtering panel** | Visible only when the file declares `professional` rows. Shows a breakdown (total / inactive-in-source / agenda-only columns / no activity in 24m), a numeric input for *minimum activity months* (default 24), plus three checkboxes: exclude agenda-only columns, exclude staff inactive in the source, and an opt-in "import only dentists and hygienists". Filtered staff are still imported as users (so historical appointments, treatments, budgets and payments keep resolving) but with `is_active=False` and the `assistant` role, which removes them from the agenda's clinician list. Reactivate individual users from **Settings → Users** afterwards. |
| **Verifactu checkbox** | Visible only when Verifactu is installed AND the file contains legal hashes. |
| **Confirm button** | Triggers `POST /execute`. Gated by `migration_import.job.execute`. |
| **Progress**     | While `status = executing`, shows *X of Y entities*. Polls every 2 s. |

## What lands where

- **Source rows that map cleanly to a destination catalog item** become
  proper odontogram treatments + plan items.
- **Free-text memos and non-clinical entries** (Gesdén `TtosMed` rows
  without an `IdTto` link, plus the *Anotación*, *Nota Económica*,
  *Higiene*, *Panorámica*, *Bonos*, *Primera Visita*… types) land as
  **administrative notes on the patient's Summary tab** instead of
  fake "Tratamiento general" tiles. The original text is preserved
  verbatim; authorship goes to the source clinician when resolvable,
  otherwise to the admin who launched the import.

## Permissions

The page itself requires `migration_import.job.read`. The **Confirm**
button is disabled for any role without `migration_import.job.execute`.

## Screenshots

_(none yet — capture when first deployed)_
