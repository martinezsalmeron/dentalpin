# Changelog — patient_timeline module

## Unreleased

- Added per-module `CLAUDE.md` for AI-agent context (2026-04-27).

### Added (plan/budget workflow rework, 2026-04-29)

- Subscribed to 8 new cross-module events with snapshot payloads:
  `treatment_plan.{confirmed,closed,reactivated}` and
  `budget.{rejected,expired,renegotiated,viewed,reminder_sent}`. All
  rendered as Spanish-titled timeline entries; no upstream ORM imports.

## 0.1.0 — initial

- Unified activity log per patient.
- Subscribes to 22 events across the system.
- Append-only model with archive instead of delete.
