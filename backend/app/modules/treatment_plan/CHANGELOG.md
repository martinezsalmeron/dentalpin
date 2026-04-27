# Changelog — treatment_plan module

## Unreleased

- Added per-module `CLAUDE.md` for AI-agent context (2026-04-27).
- Documented two string-literal events (`treatment_plan.items_reordered`,
  `treatment_plan.unlocked`) that are not yet in the `EventType` enum.

## 0.1.0 — initial

- Treatment plan CRUD with status workflow.
- Items linked to catalog services and odontogram tooth treatments.
- Clinical notes at plan and item level with media attachments.
- Bidirectional sync with `budget` via events.
- Subscribes to `appointment.completed`, `budget.accepted`,
  `odontogram.treatment.performed`.
