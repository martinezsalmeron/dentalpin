# Changelog — schedules module

## Unreleased

- feat(agents): expose `tools.py` — `get_availability` (READ) wrapping
  `AvailabilityService.resolve` (open working windows for a day; the
  agent combines it with `agenda.get_day_overview` to find gaps). Issue
  #81 P0 batch.
- feat(agents): add `find_free_slots` (READ) — real bookable gaps for a
  professional (open hours minus booked appointments), filterable by
  duration / part-of-day / window, nearest first. Reads agenda
  appointments (agenda is in `depends`). Issue #81 P1 batch.

- refactor(perms): migrate hardcoded ``can('schedules.{clinic_hours.write, professional.read, professional.write, professional.own.write}')`` strings in ``ClinicHoursPage`` and ``ProfessionalSchedulesPage`` to ``PERMISSIONS.schedules.*`` (new entries in the host permissions config).
- Settings UI migrated to host's settings registry: clinic-hours and
  professional-schedules are now registered as cards/pages under
  `/settings/workspace`. Replaces the legacy `settings.sections` slot
  and the `pages/settings/*.vue` file-based routes (2026-04-28).
- Added per-module `CLAUDE.md` for AI-agent context (2026-04-27).

## 0.1.0 — initial

- Clinic weekly schedule + per-day overrides.
- Per-professional weekly schedule + overrides.
- `/api/v1/schedules/availability` resolver consumed by the agenda
  frontend with a 404-tolerant composable fallback.
- Occupancy analytics computed from `appointment.*` events.
- First officially-removable optional module (issue #39).
