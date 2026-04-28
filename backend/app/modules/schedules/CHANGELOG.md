# Changelog — schedules module

## Unreleased

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
