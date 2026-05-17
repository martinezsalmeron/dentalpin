# migration_import — changelog

## Unreleased

- Initial version of the DPMF importer (issue #78).
  - Accepts `.dpm`, `.dpm.zst`, `.dpm.enc`, `.dpm.zst.enc`.
  - Parses 32 canonical entity types per DPMF v0.1 spec.
  - Idempotency table (`entity_mappings`) keyed by
    `(clinic_id, source_system, canonical_uuid, entity_type)` so
    re-imports are no-ops.
  - Binary ingestion endpoint (`POST /jobs/{id}/binaries`) for the
    out-of-band sync agent. Resolves by sha256 against the `_files`
    manifest and hands off to `media.DocumentService`.
  - `verifactu` integration is runtime-tolerant — the fiscal-document
    mapper skips legal-hash preservation when verifactu is not
    installed or the operator opts out.
  - Five real mappers (patient, professional, document, payment,
    fiscal_document); everything else lands in `raw_entities` until a
    dedicated mapper is added.
