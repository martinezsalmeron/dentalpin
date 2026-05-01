# Changelog — recalls module

## Unreleased

- Initial release. Patient call-back workflow (issue #62).
- Tables: `recalls`, `recall_contact_attempts`, `recall_settings`
  on the `recalls` Alembic branch (`rec_0001`).
- Endpoints under `/api/v1/recalls/*` — list, create (duplicate
  guard), detail, snooze, cancel, mark-done, log-attempt, link
  appointment, settings, dashboard stats, suggestions/next, CSV
  export.
- Events published: `recall.created`, `recall.completed`,
  `recall.snoozed`, `recall.cancelled`. `recall.due` enum value
  reserved for a future cron — not published in V1.
- Events consumed: `appointment.scheduled` (auto-link),
  `appointment.completed` (auto-close), `appointment.cancelled`
  (revert), `treatment_plan.treatment_completed` (suggestion hook,
  stateless), `patient.archived` (move active → needs_review).
- Frontend layer registers slot entries in:
  - `patient.summary.actions` — "Set recall" button
  - `patient.summary.feed` — recall pill + recent history
  - `odontogram.condition.actions` — per-treatment "Set recall"
  - `appointment.completed.followup` — "Schedule recall?" prompt
  - `dashboard.attention` — due/overdue/conversion widget
  - `settings.sections` — reason-interval + category-map editor
- Permissions: `recalls.{read,write,delete}`. Receptionist + dentist
  + hygienist + assistant get read+write; admin gets `*`.
- `installable=True`, `auto_install=True`, `removable=True`.
  Round-trip uninstall test verifies all three tables drop cleanly.
- Sidebar entry registered via `manifest.frontend.navigation`
  (`/recalls`, icon `i-lucide-bell`, gated by `recalls.read`,
  `order: 25` — between `Agenda` and `Planes de tratamiento`).
  Host i18n adds `nav.recalls` for ES/EN.
