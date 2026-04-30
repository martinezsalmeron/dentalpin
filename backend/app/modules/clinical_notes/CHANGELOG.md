# Changelog — clinical_notes

## Unreleased

### Fixed

- `DiagnosisNotesSidebar` no longer highlights every note without a
  tooth on load. The previous `selectedTooth === tooth_number` check
  matched `null === null` when no tooth was selected, painting a blue
  `ring-2 ring-primary` around all administrative / non-tooth-bound
  diagnosis notes until a tooth was clicked.

### Added

- Demo seed (`seed.py::seed_clinical_notes_demo`) wired into
  `scripts/seed_demo.py` step 7. Creates administrative + diagnosis
  notes per patient (diagnosis tooth-pinned where odontogram has data),
  `treatment_plan` notes on ~2/3 of plans and `treatment` notes on
  every other performed treatment, with author rotation between dentist
  and hygienist and time-staggered `created_at`. Inserts rows directly
  without firing events to keep `patient_timeline` re-derivation clean.
- New module owning the polymorphic `clinical_notes` and
  `clinical_note_attachments` tables (extracted from `treatment_plan`).
- `note_type` discriminator: `administrative`, `diagnosis`, `treatment`,
  `treatment_plan`.
- `tooth_number` column on `clinical_notes` for diagnosis notes
  optionally tied to a tooth.
- New owner type `treatment` — notes attach directly to the underlying
  `treatments.id` so they travel with the Treatment from diagnosis →
  plan → completion.
- Endpoints: `/notes`, `/attachments`, `/patients/{id}/recent`,
  `/patients/{id}/by-plan`, `/treatment-plans/{id}/merged`,
  `/note-templates`.
- Events: `clinical_notes.{administrative,diagnosis,treatment,plan}_created`.
- Migration `cn_0001` extends the legacy `clinical_notes` /
  `clinical_note_attachments` tables in place; backfills `note_type`
  and remaps `plan_item` notes onto the underlying `treatment` row.

### Changed

- Existing `treatment_plan.notes.*` permissions are replaced by
  `clinical_notes.notes.*`. The completion modal and per-row note UI
  in `treatment_plan` now call this module's API.

### Removed

- Notes-related endpoints, services and models from `treatment_plan`.
- `DiagnosisNotesSidebar` no longer exposes Tratamiento / Administrativas
  tabs. The composer is diagnosis-only (treatment notes belong on the
  treatment-plan UI; administrative notes are written from the patient
  Summary feed), but the listing shows **every** note type colour-coded
  via `NoteCard` so the dentist sees full context. The sidebar still
  receives `sessionTreatmentIds` in ctx but ignores it.
- `PlanNotesTimeline` redesigned: source-coloured left border on each
  card (plan = secondary, treatment = success, visit = primary), source
  icon + treatment name in the card header, and a Todas / Plan /
  Tratamiento / Visita filter row matching the patient Summary feed UX.
  The merged endpoint already returned plan + treatment + visit notes;
  the new visual makes that obvious at a glance.
