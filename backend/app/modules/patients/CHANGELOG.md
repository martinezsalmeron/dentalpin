# Changelog — patients module

## Unreleased

- Added per-module `CLAUDE.md` for AI-agent context (2026-04-27).

## 0.1.0 — initial

- Patient identity model: name, contact, demographics, `status`.
- `/api/v1/patients/*` CRUD with soft-delete via archive.
- Events: `patient.created`, `patient.updated`, `patient.archived`.
- Permissions: `patients.read`, `patients.write`.
