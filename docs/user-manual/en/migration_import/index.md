---
module: migration_import
last_verified_commit: HEAD
locale: en
---

# Data migration (dental-bridge)

The **migration_import** module imports a clinic database extracted by
[dental-bridge](https://github.com/dentaltix/dental-bridge) — patients,
appointments, budgets, payments, documents and more — into your
DentalPin clinic.

The module is optional. An admin activates it from
**Settings → Modules**, runs the migration, and may uninstall it once
the import is finished. Imported data survives uninstall — it belongs
to the regular `patients`, `payments`, `media`, … modules, not to
`migration_import` itself.

## Prerequisites

- A `.dpm` file produced by dental-bridge (any of `.dpm`, `.dpm.zst`,
  `.dpm.enc`, `.dpm.zst.enc`).
- If the file is encrypted, the passphrase used at extract time.
- The destination clinic must be selected in the top bar. The import
  always targets the *current* clinic. **Choose an empty (or near-empty)
  clinic — there is no undo.**

## Steps

1. Open **Settings → Workspace → Data migration**.
2. Upload the `.dpm` file. If it is encrypted, enter the passphrase.
3. Wait for *Validating*. The module verifies the file's integrity
   hash and refuses anything corrupted or in a future format version.
4. Review the **Preview**: entity counts, sample rows, warnings from
   the extractor, and the count of attached binaries expected.
5. If your file contains Spanish legal data (Verifactu) and the
   Verifactu module is installed, tick *"Import Verifactu legal data"*.
   For PT / FR clinics this checkbox is hidden.
6. Click **Confirm and import**. Progress is shown live.
7. The sync agent on the source machine uploads radiographs and
   documents in the background. They appear under each patient's
   *Documents* tab as they land.

## What if something goes wrong?

- **Validation failed**: the file did not pass integrity check. Most
  often a truncated upload or a wrong passphrase. Re-upload.
- **Import failed**: open *Warnings* on the job page. Each mapper
  failure is listed with the entity, source id, and error message.
- **No undo**: there is no rollback in v1. If a partial import is
  unrecoverable, restore the database from your last backup.

## See also

- [Screen reference](./screens/data-migration.md)
- Technical: `docs/technical/migration_import/`
