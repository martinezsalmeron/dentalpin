# Changelog — agenda module

## Unreleased

- feat(ux): receptionist can create a new patient inline from the *Nueva cita* modal. The patient selector dropdown surfaces a ``+ Crear paciente "<query>"`` row when the typed name doesn't match an existing record; clicking it opens a 3-field mini-form (nombre, apellidos, teléfono) that POSTs to ``/api/v1/patients`` and auto-selects the created patient. Closes the 30-second "patient on the phone" workflow. See ``docs/features/agenda-quick-patient-create.md`` and ``docs/technical/agenda-quick-patient-create.md``.
- perf(scheduler): replace ``AppointmentDailyView`` overlap-grouping loop with a union-find DSU (extracted to ``composables/calculateOverlapGroups.ts``); pre-bucket appointments by professional once; switch the per-column template ``v-for`` to a Map lookup and add ``v-memo`` so dragging an appointment no longer re-renders the other columns.
- perf(scheduler): ``useBlockedSegments`` now fetches per-professional availability in parallel via ``Promise.all`` (was sequential ``for…of``).
- perf(bundle): wrap ``AppointmentCalendar`` / ``AppointmentDailyView`` / ``AppointmentKanbanView`` / ``AppointmentMobileDayView`` in ``defineAsyncComponent``; the initial ``/agenda`` payload only ships the active mode for the current viewport.
- refactor(dx): extract ``formatLocalDate`` to ``utils/date.ts`` and remove the five duplicate copies across agenda components and the page; new ``frontend/tests/agenda/calculateOverlapGroups.test.ts`` pins the DSU output against fixtures.
- refactor(types): drop the ``as unknown as Record<string, unknown>`` cast pattern in ``useAppointments`` now that ``useApi`` accepts ``object`` payloads directly.
- refactor(perms): migrate the hardcoded ``can('agenda.appointments.write')`` gate in ``UnconfirmedPanel`` to ``PERMISSIONS.appointments.write``.
- fix(isolation): declare ``odontogram`` in ``manifest.depends``. The
  service already imported ``Treatment`` to render appointment
  treatments — the dependency was real, just undeclared.
  ``KNOWN_VIOLATIONS`` allowlist trimmed accordingly.
  (``treatment_plan`` stays as a legit known violation because
  treatment_plan depends on agenda — declaring would cycle.)
- fix(isolation): ``Appointment.patient`` no longer uses
  ``back_populates="appointments"`` — the matching attribute was
  removed from the foundational ``patients`` module. The
  relationship stays one-directional (Appointment → Patient); code
  that needs the reverse side queries agenda directly.
- perf(appointments-list): count query now hits the same indexed
  filters directly instead of materialising a subquery — drops the
  list endpoint from O(rows × eager-load tree) to O(rows) once a
  clinic crosses ~10k appointments.
- docs(user-manual): reescribir pantallas con guía operativa (ES + EN).
- **Slot uniqueness now ignores terminal statuses.** Migration
  `ag_0004` rebuilds the partial unique index
  `idx_appointment_slot` with
  `WHERE status NOT IN ('cancelled', 'completed', 'no_show')`.
  Previously the index excluded only `cancelled`, so a finished
  visit kept reserving its `(clinic, cabinet, professional,
  start_time)` slot and a fresh checked-in appointment couldn't
  be assigned to that cabinet. Slot competition now only applies
  among truly active statuses.
- New frontend slot mount **`appointment.completed.followup`** in
  `AppointmentQuickActions.vue` (issue #62). After a successful
  transition to `completed`, agenda renders a follow-up modal whose
  body is filled by any sibling module registered into the slot
  (e.g. `recalls` "Schedule a recall?" prompt). Modal stays hidden
  when no module has registered into the slot — no behaviour change
  for clinics that don't install recalls.

- Week view (`AppointmentCalendar`) now paints `clinic_closed` ranges per
  day as a hatched overlay, matching the daily view. Late-start mornings,
  early-close evenings, midday gaps and fully-closed days are all
  visually blocked instead of looking bookable. Slot math extracted into
  the new `useBlockedSegments` composable; daily view refactored to use
  it, dropping inline duplication.
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
