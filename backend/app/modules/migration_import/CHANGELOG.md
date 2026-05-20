# migration_import — changelog

## Unreleased

- feat(mappers): new ``PatientAlertMapper`` materialises Gesdén
  ``AlertPac`` rows (free-text medical history) into structured
  ``patients_clinical`` records — historical empty "Historial médico"
  on every imported patient was directly caused by ``patient_alert``
  falling through to the ``RawEntity`` catch-all.
  The classifier (``_alert_classifier.py``) routes each free-text
  alert through a cascade of Spanish medical regex rules and
  dispatches into the right destination row:
  - ``allergy``        → ``patients_clinical.Allergy`` (one row per
                          listed allergen, ``ALERGIA:`` prefix
                          recognised)
  - ``medication``     → ``patients_clinical.Medication`` (``MEDICACION:``
                          prefix + bare ``DRUG <DOSE>`` heuristic;
                          ``MG/MCG/G/ML/UI`` dose tokens stripped into
                          the ``dosage`` column)
  - ``disease``        → ``patients_clinical.SystemicDisease`` (covers
                          hipertensión / diabetes / hepatitis / cancer
                          / cardiopatía / Parkinson / Alzheimer /
                          asma / epilepsia / depresión / trastornos /
                          sinusitis / psoriasis / glaucoma /
                          osteoporosis / anemia / fibromialgia /
                          tiroides …)
  - ``anesthesia``     → ``MedicalContext.adverse_reactions_to_anesthesia``
                          + ``anesthesia_reaction_details``
  - ``smoking``        → ``MedicalContext.is_smoker`` + ``smoking_frequency``
  - ``pregnancy`` / ``lactating`` → ``MedicalContext`` flags
  - ``anticoagulant``  → ``Medication`` row + flips
                          ``MedicalContext.is_on_anticoagulants``
                          (Sintrom / Pradaxa / Adiro / Plavix /
                          Clopidogrel / Xarelto / Eliquis / Heparina /
                          Warfarina / Aldocumar)
  - ``bruxism``        → ``MedicalContext.bruxism``
  - ``administrative`` → silently skipped with an info warning
                          (``PRESU.``, ``DTO``, ``COBRAR``,
                          ``ENVIAR FACTURA``, ``VIENE REFERIDO`` …)
  - ``general``        → falls back to ``Patient.notes`` so the
                          clinician sees the original text in
                          context
  Rules are case- and accent-insensitive and ordered by precedence
  (pregnancy / lactation before generic disease, anticoagulant
  before generic medication, etc.). ``MedicalContext`` is lazily
  upserted per patient so a patient with multiple flag-style alerts
  (smoking + pregnancy + anesthesia + …) ends up with one row that
  accumulates every flag.
  Manifest grows ``patients_clinical`` in ``depends``. Validated on
  200 random alerts: 82 % routed into structured clinical buckets,
  18 % marked administrative or falling back to notes (matches the
  intuition for free-text leftover noise like "CALCIO" or "NO TIENE
  VESICULA").
- feat(applied_treatment): rescue completion status for treatments
  Gesdén left as ``StaTto=3`` despite being long done. In the live
  export ~26 k clinical treatments sit at ``StaTto=3`` (planned)
  with ``FecFin`` null — 87 % of them are 2+ years old and 55 % are
  5+ years old, which is implausible for genuinely-unstarted work.
  Investigation of the Gesdén schema found no reliable signal in
  this clinic's data (DCitasTto + TtosMed_PagoCli are empty,
  Pendiente is 0 for every row regardless of state, FechaValida /
  IdColValida / NumDocUnico / SesRealiz are all null). The clinic
  simply never updates ``StaTto`` after performing a treatment.
  The mapper now applies a heuristic on top of the formal signals:
  formal "done" (StaTto ∈ {5, 6} or FecFin set), plus
  ``FecIni`` older than 5 years (age alone), plus ``FecIni`` older
  than 2 years AND notes longer than the 40-char catalog-name floor
  (age + clinical detail). Every heuristic hit emits an audit
  warning (``completed_by_age`` / ``completed_by_notes``) so the
  operator can spot-check the reclassification. Validated on the
  una paciente de ejemplo record: 25 stale "planned" items
  collapse to 5 (the recent 2024 entries and one 2021 short-note
  case), with the other 20 promoted to completed.
- fix(applied_treatment): migrated plans land in ``active`` instead of
  ``draft``. Gesdén plans are historical, post-acceptance records —
  leaving them in DentalPin's pre-confirmation state forced the
  operator to manually confirm every imported plan before any
  consumer (budgets, payments, reports) treated it as real. ``active``
  is the natural post-acceptance state in the plan machine and is
  set directly on the model (bypassing the ``draft → pending →
  active`` event chain that would fire spurious notifications for
  historic data).
- fix(applied_treatment): treat ``StaTto`` codes ``{5, 6}`` as
  realised, not just ``5``. Code 6 is a low-volume variant that also
  carries ``FecFin`` in the source and corresponds to a completed
  treatment. The previous "code 5 only" rule made a handful of
  finished items show as pending.
- fix(applied_treatment_phase): mirror the parent ``PlannedTreatmentItem``
  status when the source phase row doesn't carry a realised
  ``StaTto`` itself. In the observed Gesdén export every phase row
  stays at ``StaTto`` 1 or 3 even when its parent treatment is
  finished — Gesdén tracks completion at the ``TtosMed`` level, not
  per ``TtosMedFases``. Without the inheritance, sessions of
  completed items stayed ``pending`` and dragged item-level
  earned-ledger semantics off.
- feat(applied_treatment): map Gesdén ``IdTipoOdg`` to DentalPin's
  ``TreatmentType`` enum (implant / crown / bridge / extraction /
  filling_composite / root_canal_full / veneer / sealant / band /
  bracket / post / apicoectomy …) instead of hard-coding
  ``"migrated"`` on every imported treatment. The UI now surfaces
  real labels; the catalog item name follows via the existing
  ``catalog_item_id`` link.
- feat(applied_treatment): skip non-clinical Gesdén timeline entries
  (Anotación, Nota Económica, Primera Visita, Higiene, Panorámicas,
  Teleradio, Fluorización, Genérico, tooth-state codes). They aren't
  tooth treatments and were polluting the migrated plan with empty
  line items. A ``applied_treatment.non_clinical_entry`` warning
  records each skip; the canonical row still lands in
  ``RawEntity`` for audit.
- feat(applied_treatment): group migrated plans by source budget
  (one plan per ``Migrado — <budget_number>``) when
  ``budget_line_uuid`` resolves; fall back to per-year buckets
  ("Migrado — 2017") when the source carries no budget link, so a
  patient with twenty years of history no longer ends up with a
  single 131-item mega-plan. The ``TreatmentPlan.budget_id`` link is
  also set so the budget detail sidebar reflects the migration.
- fix(applied_treatment): bypass ``TreatmentPlanService.create``
  because its ``count(*)``-based ``plan_number`` generator collides
  any time historic plans leave gaps in the sequence (and the
  per-budget split creates many plans per patient in one session).
  Use deterministic synthetic numbers (``MIG-<budget_number>`` or
  ``MIG-<patient_short>-<year>``) — unique by construction, idempotent
  on re-run.
- feat(applied_treatment): create per-tooth ``TreatmentTooth`` rows
  from the new ``payload["teeth"]`` field that dental-bridge emits
  (FDI numbers decoded from Gesdén's ``PiezasAdu`` / ``PiezasLec``
  bit-masks). ``ToothRecord`` rows are lazily created per ``(clinic,
  patient, tooth_number)`` so subsequent treatments on the same tooth
  reuse the same record. Surfaces remain ``None`` until the source
  ``ZonasPieza`` encoding is field-validated.
- feat(budget_line): write the first decoded FDI tooth into
  ``BudgetItem.tooth_number``; the remaining teeth (e.g. bridge
  members) land in the line ``notes`` field so the operator can split
  the budget line manually if their workflow expects a per-tooth row.
- fix(payment): the historical Payment mapper was producing rows that
  violated three NOT NULL columns on ``payments.Payment``:
  ``currency`` (snapshot of ``Clinic.currency``), ``recorded_by`` (FK
  to ``users``), and ``payment_date`` when the source row had no
  parseable date. ``currency`` is now resolved once per clinic and
  cached, ``recorded_by`` defaults to ``ctx.created_by`` (the admin
  who launched the job), and the date falls back to today with the
  notes field carrying the migration provenance. While here, fix two
  field-name regressions: the canonical payload exposes ``paid_on``
  (not ``paid_at``) and a numeric ``payment_kind`` code (not the
  English string ``method``); both are now read and the Gesdén
  ``Tipo`` code is decoded against ``_PAYMENT_KIND_MAP`` so real
  ``cash``/``card``/``bank_transfer`` etc. land in DentalPin instead
  of every payment defaulting to ``other``.
- feat(mappers): new ``PatientClientLinkMapper`` plus client→patient
  resolution in ``PaymentMapper``. In Gesdén ``DCobros`` references
  the *client* (payer), not the patient — DentalPin's flat
  ``Payment.patient_id`` couldn't be derived from the canonical row
  alone. The new mapper walks ``patient_client_link`` payloads and
  writes a secondary ``patient_for_client`` mapping (one row per
  client, ON CONFLICT DO NOTHING so the first patient registered per
  client wins) plus its primary ``patient_client_link`` mapping for
  idempotent re-runs. ``PaymentMapper`` now resolves
  ``client_uuid → patient_id`` via that sidecar before falling back
  to a direct ``patient_uuid``. Ambiguous clients (multiple patients
  linked) emit a ``patient_client_link.ambiguous_payer`` info
  warning so the operator can reconcile manually.
- feat(catalog): reuse existing DentalPin catalog items when the
  imported Spanish name matches an active item (1:1, case- and
  whitespace-normalised). On a unique match the resolver mapping
  points at the existing row and a ``catalog.matched_existing``
  info warning is emitted; ambiguous or missing matches still fall
  through to the "Importado de Gesdén" create path. This preserves
  pricing strategy, session template, VAT and odontogram mapping for
  treatments the clinic already had configured.
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
