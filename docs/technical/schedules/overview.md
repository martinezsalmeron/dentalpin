---
module: schedules
last_verified_commit: 0e9a0ac
---

# Schedules — technical overview

Clinic and professional operating hours, overrides, availability resolver,
occupancy analytics. **First officially-removable optional module.**
Issue #39 — ADR 0002 lessons applied.

## What this module owns

- Clinic-wide opening hours (default + per-day overrides).
- Per-professional working hours and time-off overrides.
- Availability resolver — given a date/time/professional, returns the
  set of bookable slots after applying every layer of overrides.
- Occupancy analytics — derived view over agenda's appointments.

## Models

- `ClinicHours` — weekday × time-range, plus a "closed" flag.
- `ClinicOverride` — date-bounded override of clinic hours.
- `ProfessionalHours` — per-user weekday template.
- `ProfessionalOverride` — date-bounded override per user.
- `OccupancyAggregate` — denormalised counts per (professional, day,
  hour) recomputed from agenda events.

Source: `backend/app/modules/schedules/models.py`.

## Direction of integration (critical)

`manifest.depends = ["agenda"]` — schedules **reads** appointment data
through events. Agenda **must never** declare `depends: ["schedules"]`,
otherwise schedules becomes mandatory and the uninstall story collapses.
Integration goes one way:

- Schedules → consumes agenda events (`appointment.{scheduled,updated,cancelled}`).
- Agenda's frontend → calls `GET /api/v1/schedules/availability` with a
  404-tolerant fallback (legacy 08:00–21:00 bounds when uninstalled).

This is the canonical example of a removable optional module — see
[ADR 0002](../../adr/0002-per-module-alembic-branches.md) for the
infra side and the module CLAUDE notes for the data-flow rule.

## Frontend surface

The module ships **no Nuxt pages** under `pages/`. Instead, two settings
pages are registered with the host shell at runtime via
`registerSettingsPage(...)` from
`backend/app/modules/schedules/frontend/plugins/settings.client.ts`:

| Mount path | Component | Permission gate |
|---|---|---|
| `/settings/workspace/clinic-hours` | `ClinicHoursPage.vue` | `schedules.clinic_hours.read` |
| `/settings/workspace/professional-schedules` | `ProfessionalSchedulesPage.vue` | `professional.read` ∪ `professional.own.read` |

These are user-facing surfaces but live under the host's
`[category]/[page].vue` route, not under the schedules module's own
`pages/`. The
[user-manual landing page](../../user-manual/en/schedules/index.md)
describes them in prose; per-screen MD files are not required because
they don't appear in `<module>/frontend/pages/**`.

## Lifecycle

- `installable=True`, `auto_install=True`, `removable=True`.
- `uninstall()` drops schedules tables; agenda continues to function via
  the 404-tolerant fallback in its availability composable.
- Migrations live on the `schedules` Alembic branch — see ADR 0002.
- Tests: `backend/tests/test_uninstall_roundtrip.py` keeps the round-trip
  green. Don't break it.

## Gotchas

- **Occupancy is a derived view.** Source of truth for appointments
  remains in agenda. Never write back from here.
- **Receptionists read analytics; hygienists do not.** Don't widen.
- **Adding new code must keep the uninstall round-trip green.**

## Related ADRs

- [`0001` — modular plugin architecture](../../adr/0001-modular-plugin-architecture.md)
- [`0002` — per-module Alembic branches](../../adr/0002-per-module-alembic-branches.md)
- [`0003` — event bus over direct imports](../../adr/0003-event-bus-over-direct-imports.md)

## See also

- [Events](./events.md)
- [Permissions](./permissions.md)
- Module CLAUDE notes: [`backend/app/modules/schedules/CLAUDE.md`](../../../backend/app/modules/schedules/CLAUDE.md).
