# Agenda module

Appointments, scheduling, cabinets. Owns the `Appointment` entity and
its state machine.

## Public API

Routes mounted at `/api/v1/agenda/`. See `router.py` for the full
surface (appointments CRUD, transitions, cabinet assignments, kanban).

## Dependencies

`manifest.depends = ["patients", "catalog"]`.

## Permissions

`agenda.appointments.{read,write}`, `agenda.cabinets.{read,write}`.

## Events emitted

- `appointment.scheduled` — new appointment
- `appointment.updated` — generic update
- `appointment.status_changed` — published alongside specific status events; payload carries `from_status`/`to_status`/`changed_at`/`changed_by`
- `appointment.cabinet_changed` — cabinet (re)assignment, payload includes `from_cabinet_id`/`to_cabinet_id` (nullable)
- `agenda.visit_note_updated` — visit-level note (reuses `AppointmentTreatment.notes`)

## Events consumed

None.

## Lifecycle

- `removable=False`. Most modules depend on appointments.

## Gotchas

- **Schedules must NOT be a dependency.** The `schedules` module depends
  on agenda; the data flow is one-way. Never declare
  `depends: ["schedules"]` here. See `schedules/CLAUDE.md`.
- **Status transitions go through `AppointmentService.transition`** —
  it publishes both the specific status event and the generic
  `appointment.status_changed`.
- **Cabinet assignment uses `assign_cabinet`** — it publishes
  `appointment.cabinet_changed` with both old and new ids.
- **Mobile free-slot computation is client-side** (#61). The composable
  `frontend/composables/useFreeSlots.ts` derives gaps from already-loaded
  appointments + the optional `schedules` availability payload. Do not
  add a backend free-slot endpoint without ADR — the data flow stays
  client-side and the schedules dependency stays optional.

## Related ADRs

- `docs/adr/0001-modular-plugin-architecture.md`
- `docs/adr/0003-event-bus-over-direct-imports.md`

## CHANGELOG

See `./CHANGELOG.md`.
