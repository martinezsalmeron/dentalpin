# Changelog — agenda module

## Unreleased

- `GET /api/v1/agenda/appointments` now accepts a `patient_id` filter.
  Previously the patient-detail Citas tab passed `patient_id` but the
  endpoint silently ignored it and returned the whole clinic's
  appointments. `AppointmentService.list_appointments` gained a
  keyword-only `patient_id` argument.
- Patient detail → Clínica → Citas: `AppointmentsMode` paginates with
  the shared `PaginationBar` at page_size=20, dropping the hard-coded
  page_size=100 single-page dump.
- Added per-module `CLAUDE.md` for AI-agent context (2026-04-27).
- Mobile agenda: surface free slots for quick emergency booking (#61).
  - New composable `useFreeSlots` computes busy/free/blocked timeline
    entries client-side from appointments + schedules availability.
  - New components `AppointmentMobileTimeline` and
    `AppointmentMobileDaySummary`. Single-track UX (one professional or
    one cabinet at a time), persisted in `localStorage`.
  - Min-duration filter chips (15/20/30/45/60+) hide noisy short gaps;
    short gaps render as faded pills.
  - Free-slot tap pre-fills the appointment composer with start time,
    duration and resource (professional or cabinet).
  - `AppointmentModal` now takes an optional `initialCabinet` prop and
    renders fullscreen on mobile with larger tap targets.

## 0.4.0 — initial documented version

- Appointment CRUD with full state machine.
- Cabinet assignment with `appointment.cabinet_changed` events.
- Visit-level notes via `AppointmentTreatment`.
- Kanban view backed by `kanban_service`.
