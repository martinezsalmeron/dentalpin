# Architecture Decision Records

Why we record decisions here:

- The repo grows; the *why* behind a constraint stops being obvious.
- AI agents and new contributors need durable, searchable context for
  rules they will otherwise question or accidentally undo.
- `git log` carries the *what*. ADRs carry the *why* + the *trade-offs
  considered* + the *consequences* if you break the rule.

## Convention

- Filename: `NNNN-kebab-title.md` — zero-padded sequence, never reused.
- One decision per file. Short. ≤1 page when possible.
- Every ADR uses the same structure: see `TEMPLATE.md`.
- Status: `proposed` → `accepted` → optionally `superseded by NNNN` /
  `deprecated`. Never delete an ADR; supersede it.
- Date: the date status changed (ISO `YYYY-MM-DD`).
- Cite source files (`path:line`) and tests so the rule is verifiable.

## ADR vs `docs/design/`

- `docs/adr/` — historical decisions that shape today's code. Read to
  understand why a rule exists.
- `docs/design/` — forward-looking design briefs and technical plans.
  Read while a feature is being shaped. Some may graduate to an ADR
  once the decision is locked in.

## When to write a new ADR

Triggers (any one):

- A rule has been broken once and we want to make sure it isn't again.
- A reviewer asked "why is it this way?" and the answer isn't in code.
- We chose between two reasonable approaches and the loser will keep
  resurfacing.
- A constraint is imposed by an external system (regulator, vendor,
  licensor) and we need to capture it once.

## Index

| #    | Title | Status | Date |
|------|-------|--------|------|
| 0001 | [Modular plugin architecture](0001-modular-plugin-architecture.md) | accepted | 2026-04-27 |
| 0002 | [Per-module Alembic branches](0002-per-module-alembic-branches.md) | accepted | 2026-04-27 |
| 0003 | [Event bus over direct cross-module imports](0003-event-bus-over-direct-imports.md) | accepted | 2026-04-27 |
| 0004 | [BSL 1.1 license, Apache 2.0 after 4 years](0004-bsl-license.md) | accepted | 2026-04-27 |
| 0005 | [Relative permissions, registry-prefixed namespacing](0005-relative-permissions.md) | accepted | 2026-04-27 |
| 0006 | [Budget public link two-factor authentication](0006-budget-public-link-2-factor-auth.md) | accepted | 2026-04-28 |
