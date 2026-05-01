# Changelog — patients module

## Unreleased

- **`do_not_contact: bool` flag** added to the patient model
  (issue #62, recalls). Operational opt-out — patients with this flag
  set are excluded from the recalls call list and any future
  outreach automation. Defaults to `false`. Editable from the
  Demographics edit modal. Migration: `pat_0002`.
- New slot mount `patient.summary.actions` rendered on
  `PatientSummaryHero` so sibling modules (e.g. `recalls`) can
  contribute action buttons to the patient summary without modifying
  the patients module UI.

- Patient detail → Administración → Presupuestos: paginated (page_size=20).
  `AdministrationTab` now owns its own paginated fetch via the shared
  `PaginationBar`; the parent `[id].vue` no longer prefetches budgets.
- Added per-module `CLAUDE.md` for AI-agent context (2026-04-27).
- Issue #60: patient detail page lands on a new **Summary** tab by
  default (replaces Info as default; Info stays accessible via tab
  list and `?tab=info`). Summary renders `patient.summary.feed` slot —
  filled by the clinical_notes module.
- Removed left sidebar (`PatientQuickInfo`) from patient detail. All
  tabs now span full width. Sidebar widgets (avatar, status, alerts,
  contact strip, active plan, next appointment, emergency contact)
  collapsed into a new `PatientSummaryHero` rendered at the top of
  the **Summary** tab. The `patient.detail.sidebar` slot is preserved
  by re-mounting it inside the hero so community modules keep their
  extension point.
- **Summary** tab now uses a 2-column layout: a sticky left rail
  (`PatientSummaryHero`) and a main column for the clinical-notes feed.
  Other tabs (info, clinical, administration, timeline) keep their
  full-width layout.

## 0.1.0 — initial

- Patient identity model: name, contact, demographics, `status`.
- `/api/v1/patients/*` CRUD with soft-delete via archive.
- Events: `patient.created`, `patient.updated`, `patient.archived`.
- Permissions: `patients.read`, `patients.write`.
