# 0002 — Per-module Alembic branches

- **Status:** accepted
- **Date:** 2026-04-27
- **Tags:** modules, migrations, uninstall

## Context

Removable modules need a clean uninstall path: drop their tables, drop
their migration history, leave the rest of the schema intact. With a
single shared Alembic chain, downgrading a removable module's first
migration walks back through every later migration that happened to land
after it — including migrations belonging to *other* modules. That
breaks any module whose revisions were threaded through another's chain.

Issue #56 captured a regression where this exact failure mode broke the
uninstall round-trip. Fix: each module owns its own Alembic branch via
`branch_labels`, and the loader reconstructs `version_locations`
dynamically from the modules currently installed.

## Decision

Every module's first migration sets `branch_labels = ("<module>",)`.
Every later migration in that module is on the same branch (its
`down_revision` always points to a revision in the same branch).

Operational implications:

- `alembic upgrade heads` (plural) is the canonical command.
- `alembic upgrade head` is wrong here and may pick an arbitrary branch.
- Cross-module FKs are still allowed but only against modules listed in
  `manifest.depends` (so we know the dep was up before us).
- The loader uses `_module_branch_label()` to detect a module's branch
  and assemble `version_locations` per active install.

## Consequences

### Good

- Uninstall round-trip works without rewriting unrelated history
  (`backend/tests/test_uninstall_roundtrip.py`).
- Adding or removing a module never breaks another module's history.
- New modules can be developed independently without merge conflicts on
  a global Alembic file.

### Bad / accepted trade-offs

- Authors must remember `branch_labels` on the first migration of every
  module. CI now catches the missing case.
- `alembic upgrade head` (singular) is footgun in this repo — always use
  `heads`.

## Alternatives considered

- **Global linear chain.** Rejected: caused #56, makes uninstall unsafe.
- **One Alembic env per module.** Rejected: too much boilerplate, breaks
  ad-hoc tooling that assumes one env.

## How to verify the rule still holds

- `backend/tests/test_alembic_branches.py` — discovery + branch isolation
- `backend/tests/test_alembic_roundtrip.py` — full upgrade/downgrade cycle
- `backend/tests/test_uninstall_roundtrip.py` — the regression test
- `backend/app/core/plugins/processor.py:483` — `_module_branch_label`

## References

- Issue #56
- `docs/technical/creating-modules.md` §3 (`migrations/`)
- Alembic branch labels docs: <https://alembic.sqlalchemy.org/en/latest/branches.html>
