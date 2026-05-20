# migration_import — changelog

## Unreleased

- fix(routing): correct the route prefix used by the frontend wizard and
  by the inline docs/CLAUDE.md/user-manual frontmatter. FastAPI mounts
  the router under ``/api/v1/migration_import/`` (the manifest name,
  with the underscore), but the Vue page, the docstrings and the
  ``related_endpoints`` frontmatter referenced
  ``/api/v1/migration-import/``. The settings wizard was therefore
  silently 404'ing on every step; only ``curl`` against the real path
  worked. All five callers in ``DataMigrationPage.vue`` plus
  ``binaries/ingest.py``, ``router.py``, ``CLAUDE.md`` and both locale
  user-manual files are now aligned.
- fix(lifecycle): default ``_staging_root()`` to
  ``{STORAGE_LOCAL_PATH}/migration-import`` instead of
  ``/var/lib/dentalpin/migration-import``. The previous hardcoded path
  was outside any volume the backend container can write to (running
  as ``appuser``), so installing the module failed with ``[Errno 13]
  Permission denied`` on a stock docker-compose setup. The
  ``MIGRATION_IMPORT_STAGING_DIR`` override is unchanged.
- refactor(perms): migrate hardcoded ``can('migration_import.job.execute')`` in ``DataMigrationPage`` to ``PERMISSIONS.migrationImport.jobExecute``.
- refactor(errors): switch ``catch (err: any)`` to ``catch (err: unknown)`` + shared ``errorMessage`` helper in the upload flow.
- perf(lists): drop the ``select_from(query.subquery())`` count
  anti-pattern in ``ImportJobService.list_jobs``,
  ``list_warnings`` and the warnings-count after each execute. All
  counts now run directly over the indexed filter set.
- chore(events): publisher helpers (``publish_job_started``,
  ``publish_job_completed``, ``publish_job_failed``,
  ``publish_binary_resolved``, ``publish_entity_persisted``) are now
  ``async`` and await the bus inline. Callers in the mapper pipeline
  and binary ingest endpoint were updated to ``await``.
- chore(events): subscribe to ``migration.entity.persisted`` via
  ``EventType.MIGRATION_ENTITY_PERSISTED`` instead of a string
  literal.
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
