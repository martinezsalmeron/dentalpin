# migration_import — changelog

## Unreleased

- feat(payment): split a Gesdén ``PagoCli`` across every patient
  linked to its payer client. The mapper used to attribute the whole
  amount to the first patient mapped, inflating that patient's credit
  while leaving family members in apparent debt. Now
  ``PatientClientLinkMapper`` exposes the full M:N graph through
  ``ctx.client_to_patients``; the payment mapper splits each amount
  proportionally to each linked patient's existing ``earned`` ledger
  (or evenly when nobody has earned activity yet). The resolver
  maps the source canonical_uuid to the first split share; the rest
  are unmapped audit rows. Emits a ``payment.split_across_family``
  warning per split for the operator to spot-check.
- fix(applied_treatment): allow negative earned amounts (credit-note
  corrections from Gesdén's ``Nota Económica`` rows). The
  ``ck_earned_amount_nonneg`` check was lifted in ``pay_0003`` so the
  ledger sums net out correctly against the matching payments;
  publishers still emit positive amounts in normal flow.
- fix(applied_treatment): mirror billable non-clinical Gesdén entries
  (hygiene, panoramic X-rays, fluorisation, "Bonos", first-visit
  consultations, generic services — ``IdTipoOdg`` in
  ``_NON_CLINICAL_TIPO_ODG``) into ``PatientEarnedEntry``. The mapper
  was dropping these rows entirely so the odontogram chart stayed
  clean, but their ``Importe`` was a real billed amount; ignoring it
  left the matching payment on the ledger without a counterpart and
  inflated patient credit across the board. Treatment /
  PlannedTreatmentItem are still skipped — only the financial row is
  recorded, with a stable uuid5 ``treatment_id`` so re-runs stay
  idempotent under the ledger's unique constraint.
- feat(budget): preserve the source budget number. The mapper now
  composes ``PRES-YYYY-NNNN`` from ``CanonicalBudget.number`` +
  ``quote_date.year`` (with a ``S{n}`` middle segment for non-default
  series) instead of letting the destination renumber every historic
  presupuesto into the current year. On collision with an existing
  row in the destination the auto-generator takes over and a
  ``budget.number_collision`` warning is emitted. Required a one-line
  contract change in ``BudgetService.create_budget`` to honour
  ``data['budget_number']`` when supplied.
- fix(applied_treatment): drop budget-shadow planned rows whose
  performed counterpart was created as a *new* TtosMed entry.
  Gesdén never updates ``StaTto`` 3→5 in place — when a budgeted
  line gets executed the clinician adds a second row at
  ``StaTto=5`` and the original sits at ``StaTto=3`` forever, so
  importing both flooded the odontogram with planned/performed
  twins. A single DPMF pre-pass groups by
  ``(patient, IdTto, IdTipoOdg, teeth)`` and pairs each performed
  with the nearest earlier planned inside a 24-month window; the
  planned twin is skipped and its ``canonical_uuid`` redirected
  via the resolver to the performed's ``PlannedTreatmentItem`` so
  any ``budget_line`` / ``applied_treatment_phase`` that referred
  to the planned still resolves cleanly. Clinics that update
  ``StaTto`` in place have only one row per treatment → the
  pairing never matches → no behavioural change for them.
- feat(patient): pipe ``Pacientes.Notas`` (new in dental-bridge
  adapter 0.0.2) through the same classifier that handles
  ``AlertPac.Texto``. Lines parse into ``Allergy`` / ``Medication`` /
  ``SystemicDisease`` / ``MedicalContext`` flags / administrative
  ``ClinicalNote`` rows; the unclassified remainder appends to
  ``Patient.notes``. Reuses ``PatientAlertMapper.dispatch_freetext``
  so a single rule change propagates to both sources.
- feat(applied_treatment): mirror ``TtosMed.Notas`` into the
  ``clinical_notes`` module as ``note_type='treatment'`` rows owned by
  the imported ``Treatment``. The mapper had been storing the body on
  ``Treatment.notes`` only; the patient-detail clinical feed and the
  diagnosis sidebar both read from the polymorphic ``clinical_notes``
  table, so migrated patients showed an empty clinical history even
  though ~99 % of Gesdén treatments carry narrative
  (composite shade, implant lot, anaesthetic, outcome…).
  ``created_at`` is anchored to the treatment's effective date so the
  feed renders chronologically; ``author_id`` resolves to the
  professional's User row (or the importer admin if unmapped).
- fix(applied_treatment): set ``ToothRecord.general_condition`` for
  realised treatments that leave an observable artefact
  (extraction → missing, crown/bridge/veneer/post → crown,
  implant → implant, fillings/inlays/overlays → filling,
  root canals → root_canal, sealant → sealant). Last write by
  ``end_date`` (or ``start_date`` if absent) wins; ties broken by
  precedence so an implant beats a prior extraction on the same
  tooth. Without this, the imported odontogram chart rendered
  uniformly ``healthy`` even for patients with decades of restorative
  history. Paired with the frontend filter below, the Diagnóstico
  panel stays clear and the chart actually reflects the mouth.
- fix(applied_treatment): hide migrated treatments from the
  Diagnóstico tab. Bulk-importing a patient's full history flooded
  the active diagnosis panel with hundreds of historical artefacts,
  making the "what am I diagnosing today?" workflow unusable.
  ``DiagnosisMode`` now filters
  ``source_module !== 'migration_import'``; the migrated record stays
  visible in the History tab and as PlannedTreatmentItems on the
  imported plans.
- fix(professional): map canonical role ``doctor`` → DentalPin
  ``dentist`` (was silently falling through to ``assistant``, so every
  Gesdén dentist landed as auxiliar), and create the imported User
  with ``is_active=True`` so the Users page shows them as active.
  Login stays blocked by the ``!migration_disabled:`` sentinel hash
  until the admin sends a password reset. The mapper also honours the
  canonical ``deactivated`` flag when present.
- fix(applied_treatment): only formal-done treatments enter the
  patient earned ledger. The first ledger pass counted every
  ``is_realised`` treatment (including the ones rescued by the
  age/notes heuristic), which silently inflated the clinic's
  apparent revenue and erased legitimate patient credit on
  in-progress plans. The earned ledger now gates strictly on
  ``formal_done`` (Gesdén ``StaTto ∈ {5, 6}`` or ``FecFin`` set in
  the source); heuristic-promoted treatments continue to surface as
  "completed" in the UI plan list so the clinician can review them,
  but they don't generate revenue. Validated against la paciente de ejemplo
  three-way: 16,135 € paid · 14,305 € earned-formal · 14,090 € sum
  of accepted budgets → 1,830 € patient credit, matching the
  expected up-front payment for the in-progress implant plan.
- fix(applied_treatment): write the patient earned-ledger entry
  directly. The patient balance UI reads from
  ``patient_earned_entries`` (treatments performed → money the
  clinic has earned), which is normally populated by the payments
  module's event handlers reacting to
  ``odontogram.treatment.performed`` /
  ``treatment_plan.item_session_completed``. The migration bypasses
  the services to avoid spurious notifications for historic data,
  so those events never fire and the ledger stays empty — every
  imported patient appears to be in massive credit because their
  payments are recorded but the treatments they paid for aren't
  counted. ``AppliedTreatmentMapper`` now inserts a
  ``PatientEarnedEntry`` row for every completed treatment with
  ``source_event='migration_import'`` and
  ``source_session_id=NULL`` (matches the
  ``odontogram.treatment.performed`` non-session path; our migrated
  sessions carry ``amount=0`` so the per-session ledger path would
  add nothing). Validated on una paciente de ejemplo: 39
  performed treatments × prices = 32,645 €. With 16,135 € of payments
  recorded, the balance flips from −16,135 (clinic owes the
  patient) to +16,510 (patient still owes the clinic) — which
  matches the operative reality of an in-progress implant /
  prosthesis plan.
- fix(budget): stamp the source ``FecPresup`` onto ``Budget.created_at``
  and ``Budget.updated_at`` so the UI shows the real budget date
  rather than the import-run timestamp. ``TimestampMixin`` was
  seeding both columns from ``func.now()`` because the mapper never
  overwrote them, so every migrated budget read "creado hoy" on the
  patient page regardless of whether it was quoted in 2017 or 2024.
  ``updated_at`` advances to the latest lifecycle event
  (``rejected_date`` > ``accepted_date`` > ``quote_date``) so the
  budget pipeline UI keeps sorting recently-updated entries on top
  as before.
- fix(budget): rescue ``Budget.status`` from the
  ``PresuTto.IdTtoMedOrig`` back-reference. Gesdén keeps a Presu↔TtosMed
  double link (forward in ``TtosMed.IdPresuTto``, backward in
  ``PresuTto.IdTtoMedOrig`` — exposed canonically as
  ``budget_line.applied_treatment_uuid``). Clinics with poor hygiene
  rarely fill ``Presu.FecAcepta`` even when the patient clearly
  acted on the budget, so 88 % of the live export ends up with
  Estado=0 (draft). The back-reference holds because every applied
  treatment must point at its budget line to bill correctly —
  ``BudgetLineMapper`` now promotes the parent budget from ``draft``
  to ``accepted`` (one-way) the first time it sees a line with
  ``applied_treatment_uuid`` set. Verified on una paciente de ejemplo: 8/18 budgets correctly accepted (the 2019-2024
  ones backed by 661 applied treatments, totalling 14,090 €), 10/18
  stay draft (the 2017 alternative quotes that never had work
  done).
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
  - ``administrative`` → ``clinical_notes.ClinicalNote`` with
                          ``note_type='administrative'`` attached to
                          the patient (``PRESU.``, ``DTO``,
                          ``COBRAR``, ``ENVIAR FACTURA``,
                          ``VIENE REFERIDO`` …) — preserves the
                          info in the reception-friendly notes panel
                          instead of dropping it on the floor
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
