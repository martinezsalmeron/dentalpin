# Changelog — treatment_plan module

## Unreleased

- Added per-module `CLAUDE.md` for AI-agent context (2026-04-27).
- Documented two string-literal events (`treatment_plan.items_reordered`,
  `treatment_plan.unlocked`) that are not yet in the `EventType` enum.

### Removed (issue #60 — clinical-notes extraction)

- `ClinicalNote` and `ClinicalNoteAttachment` models, schemas, service
  (`notes_service.py`) and router endpoints. Ownership moved to the new
  `clinical_notes` module.
- `treatment_plan.{plan,item}_note_created` events (replaced by
  `clinical_notes.{administrative,diagnosis,treatment,plan}_created`).
- `note_body` and `attachment_document_ids` fields from
  `CompleteItemRequest`. The client now POSTs a follow-up note to
  `/api/v1/clinical_notes/notes` after a successful completion.
- `note_templates.py` (moved into `clinical_notes`).
- Frontend components `PlanNotesTimeline.vue`, `PatientClinicalNotesByPlan.vue`,
  `useClinicalNotes` composable. Replacement components are provided by
  the `clinical_notes` Nuxt layer with the same names so existing
  imports (`<PlanNotesTimeline />`) keep resolving.

## 0.1.0 — initial

- Treatment plan CRUD with status workflow.
- Items linked to catalog services and odontogram tooth treatments.
- Clinical notes at plan and item level with media attachments.
- Bidirectional sync with `budget` via events.
- Subscribes to `appointment.completed`, `budget.accepted`,
  `odontogram.treatment.performed`.
