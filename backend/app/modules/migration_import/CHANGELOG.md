# migration_import — changelog

## Unreleased

- perf(pipeline): batch the ``processed_entities`` counter update.
  Previously every persisted entity emitted
  ``migration.entity.persisted``, which a subscriber consumed in a
  *fresh* DB session — that meant a separate ``BEGIN ... UPDATE ...
  COMMIT`` round-trip per row (~25 ms each on local Postgres), so a
  1.27 M-row import projected to ~9 h. The counter is now bumped on
  the main session once per ``_COMMIT_BATCH`` (every 500 entities),
  alongside the checkpoint write and the natural batch commit. The
  ``MIGRATION_ENTITY_PERSISTED`` event is still emitted once per
  batch (now carrying the batch ``count``) for any external
  subscriber that wants progress signals; the importer itself no
  longer subscribes. Benchmarked locally: 10 000-entity RawEntity
  slice goes from ~5 min to ~4 s (~2 600 ent/s), projecting a full
  1.27 M run to ~8 min instead of ~9 h.
- feat(mappers): new ``AppliedTreatmentMapper`` materialises DPMF
  ``applied_treatment`` into a three-table cascade — one lazy
  ``treatment_plan.TreatmentPlan`` per patient (titled
  ``"Migrado de Gesdén"``, cached for the job), one
  ``odontogram.Treatment`` per applied treatment (clinical_type
  ``migrated``, with the source price snapshotted on
  ``price_snapshot``), and the linking
  ``treatment_plan.PlannedTreatmentItem``. Tooth/surface detail is
  skipped — the canonical ``odontogram_raw`` bit-mask isn't decoded
  upstream yet.
- feat(mappers): new ``AppliedTreatmentPhaseMapper`` attaches DPMF
  ``applied_treatment_phase`` rows as
  ``PlannedTreatmentItemSession`` children of the imported plan
  item. Per-session amount is left at zero (DentalPin sessions carry
  an absolute amount; the canonical ``percent_to_bill`` is exposed
  in the session label instead — clinics can rebalance manually).
- chore(manifest): add ``odontogram`` to ``depends`` (used by
  AppliedTreatmentMapper to construct Treatment rows directly).
- feat(mappers): new ``CatalogItemMapper`` materialises DPMF
  ``treatment_catalog_item`` rows into ``catalog.TreatmentCatalogItem``.
  Items land under a lazy-created ``TreatmentCategory`` keyed
  ``"migrado_gesden"`` so the clinic can re-classify them later
  without touching the original taxonomy. ``internal_code`` is
  synthesised from the canonical UUID (``MIG-xxxxxxxx``) to dodge
  ``uq_catalog_item_clinic_code`` collisions when the source carries
  duplicate codes across tariff variants.
- feat(mappers): new ``CatalogVariantMapper`` resolves
  ``treatment_catalog_variant`` to the parent
  ``treatment_catalog_item`` (pipe-through). DentalPin's catalog
  doesn't model a per-tariff axis, so the variant's canonical UUID
  resolves to the same DentalPin row as its parent; pricing
  differences survive as ``budget_line.unit_amount`` snapshots.
- feat(mappers): new ``BudgetMapper`` + ``BudgetLineMapper`` materialise
  DPMF ``budget`` / ``budget_line`` into ``budget.Budget`` /
  ``budget.BudgetItem`` via the corresponding services. Budget header
  status is derived from ``accepted_date`` / ``rejected_date`` presence
  (canonical ``status_code`` is source-opaque). Line items resolve
  ``treatment_uuid`` → ``treatment_variant_uuid`` as the catalog FK
  fallback chain. Each line triggers ``_recalculate_totals`` on the
  parent budget so the header subtotal/total stay in sync.
- chore(base): add ``created_by: UUID`` to ``MapperContext`` (populated
  from ``ImportJob.created_by``) — required by the budget mapper and
  any future mapper whose target service tracks the acting user.
- chore(manifest): add ``catalog`` and ``budget`` to ``depends``. Both
  are real ORM imports by the new mappers, so the declaration is
  required by the modular-architecture contract.
- feat(mappers): new ``AppointmentMapper`` materialises DPMF
  ``appointment`` entities into ``agenda.Appointment`` rows. Resolves
  ``patient_uuid``/``professional_uuid`` via the
  :class:`MappingResolver`, combines ``scheduled_date`` +
  ``scheduled_time`` into a UTC ``start_time`` (computes ``end_time``
  from ``duration_minutes``, default 30), maps ``coarse_status`` →
  DentalPin's 7-state status enum, and emits warnings under
  ``appointment.{missing_actor,unmapped_actor,no_schedule,unparseable_datetime}``
  when an entity has to be skipped instead of silently dropped. Chair
  resolution is deferred until a ``catalog_item`` mapper exists.
- chore(manifest): add ``agenda`` to ``depends`` (used by the new
  appointment mapper). ``schedules`` stays as a forward-compat
  declaration even though no mapper touches it yet.
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
