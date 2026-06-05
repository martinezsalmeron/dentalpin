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

## Tools exposed

Agent tools in `tools.py` (wrap `AppointmentService`, no logic duplicated).
Write tools use `ctx.supervisor_id` (the human in the loop) for audit columns.

| Tool | Category | Wraps | Permission |
|---|---|---|---|
| `get_day_overview` | READ | `AppointmentService.list_appointments` | `agenda.appointments.read` |
| `get_appointment` | READ | `AppointmentService.get_appointment` | `agenda.appointments.read` |
| `list_cabinets` | READ | `CabinetService.list_cabinets` | `agenda.cabinets.read` |
| `list_professionals` | READ | `kanban_service._fetch_professionals` | `agenda.appointments.read` |
| `book_appointment` | WRITE | `AppointmentService.create_appointment` | `agenda.appointments.write` |
| `cancel_appointment` | DESTRUCTIVE | `AppointmentService.cancel_appointment` | `agenda.appointments.write` |

`find_free_slots` is intentionally **not** here — free-slot computation belongs to
`schedules`, which will register its own tool. Agenda does not cross that boundary.

## Frontend slots exposed

- `appointment.completed.followup` — rendered by `AppointmentQuickActions.vue`
  after a successful transition to `completed`. Sibling modules
  (e.g. `recalls`) register components that prompt the receptionist
  for a follow-up action. Modal stays hidden when no registrations
  exist. Slot ctx: `{ appointment }`.

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
