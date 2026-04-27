# Changelog — schedules module

## Unreleased

- Added per-module `CLAUDE.md` for AI-agent context (2026-04-27).

## 0.1.0 — initial

- Clinic weekly schedule + per-day overrides.
- Per-professional weekly schedule + overrides.
- `/api/v1/schedules/availability` resolver consumed by the agenda
  frontend with a 404-tolerant composable fallback.
- Occupancy analytics computed from `appointment.*` events.
- First officially-removable optional module (issue #39).
