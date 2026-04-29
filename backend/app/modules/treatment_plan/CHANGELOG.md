# Changelog — treatment_plan module

## Unreleased

- Added per-module `CLAUDE.md` for AI-agent context (2026-04-27).
- Documented two string-literal events (`treatment_plan.items_reordered`,
  `treatment_plan.unlocked`) that are not yet in the `EventType` enum.

### Added (frontend, 2026-04-29 — PR2)

- Page `/treatment-plans/pipeline` (bandeja de planes) with five
  tabs powered by the new `usePipeline` composable. Search box +
  call/WhatsApp quick-actions per row.
- Workflow modals (`components/clinical/modals/`):
  `ConfirmPlanModal`, `ReopenPlanModal`, `ClosePlanModal`,
  `ReactivatePlanModal`, `ContactLogModal`.
- `useTreatmentPlans` gains `confirmPlan`, `reopenPlan`, `closePlan`,
  `reactivatePlan`, `logContact` actions wired to the PR1 endpoints.
- `PlanDetailView` exposes `Confirm` / `Reopen` / `Reactivate` buttons
  contextual to the plan status; the legacy "Cancel plan" button now
  delegates to the unified `ClosePlanModal` (closure_reason +
  closure_note).
- Navigation entry `nav.pipeline` linked to the bandeja.
- Status filter on the plans index updated to the new state set.

### Added (plan/budget workflow rework, 2026-04-29 — PR1)

- New plan states: `pending` (between confirm and accept) and `closed`
  (terminal non-completed state) with `closure_reason`, `closure_note`,
  `closed_at`, `confirmed_at` columns.
- Workflow transitions: `confirm` (draft → pending, auto-creates draft
  budget via direct call to BudgetService), `reopen`, `close`,
  `reactivate`, plus `accept_from_budget` / `reject_from_budget` for
  the budget event handlers.
- New endpoints:
  - `POST /treatment-plans/{id}/{confirm,reopen,close,reactivate}`
  - `POST /treatment-plans/{id}/contact-log`
  - `GET  /treatment-plans/pipeline` (5-tab cross-module bandeja).
- Granular permissions `plans.{confirm,close,reactivate}`.
  Receptionist role gains close + reactivate.
- Three new events with snapshot payloads:
  `treatment_plan.{confirmed,closed,reactivated}`. Subscribers
  (patient_timeline) consume payload data only — no cross-module ORM
  reads.
- `auto_close_expired_plans` cron (daily 03:00) — closes pending plans
  whose budget has been expired beyond the per-clinic threshold.
- Plan ↔ budget direct call carve-out: `confirm()` calls
  `BudgetService.create_from_plan_snapshot` synchronously (budget is
  in `manifest.depends`). Documented in CLAUDE.md.

### Removed

- Legacy `cancelled` plan status (migrated to
  `closed` + `closure_reason='cancelled_by_clinic'`).

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
