<!--
PR template for DentalPin. The checklist enforces conventions documented
in CLAUDE.md and docs/checklists/. Tick boxes that apply; strike through
the rest. Reviewers: don't approve while a relevant box is unchecked.
-->

## Summary

<!-- 1–3 bullets. What and why, not how. -->

-

## Modules touched

<!-- e.g. patients, billing/, frontend layer for schedules, none -->

-

## Checklist

### Always

- [ ] PR title follows Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `chore:`)
- [ ] `cd backend && ruff check . && ruff format --check .` passes
- [ ] `cd frontend && npm run lint` passes
- [ ] Tests added or updated when behaviour changed
- [ ] No cross-module imports outside `manifest.depends`

### If a new module was added

- [ ] Entry point registered in `backend/pyproject.toml` (`[project.entry-points."dentalpin.modules"]`)
- [ ] `backend/app/modules/<name>/CLAUDE.md` written (purpose, public API, events, permissions, gotchas)
- [ ] `backend/app/modules/<name>/CHANGELOG.md` started
- [ ] Alembic migrations live on the module's own branch (`branch_labels=("<name>",)`)
- [ ] `python backend/scripts/generate_catalogs.py` re-run, `docs/modules-catalog.md` and `docs/events-catalog.md` updated
- [ ] If `removable=True`: uninstall round-trip test added (see `backend/tests/test_uninstall_roundtrip.py`)

### If events were added or changed

- [ ] New event added to `backend/app/core/events/types.py` `EventType`
- [ ] `python backend/scripts/generate_catalogs.py` re-run
- [ ] Payload shape documented in module CLAUDE.md (publishers + consumers)

### If permissions were added or changed

- [ ] Returned by module `get_permissions()` (no module prefix; registry adds it)
- [ ] Listed in `manifest.role_permissions`
- [ ] If user-facing: added to `frontend/app/config/permissions.ts`
- [ ] Endpoint protected with `require_permission("module.resource.action")`

### If a cross-module FK was introduced

- [ ] Target module is in `manifest.depends`
- [ ] CI `manifest-consistency` is green

### If an architectural decision was made

- [ ] ADR added under `docs/adr/NNNN-title.md` (copy `docs/adr/TEMPLATE.md`)

### If a new domain term was introduced

- [ ] Appended to `docs/glossary.md` (ES ↔ EN)

### If a touched module already exists

- [ ] Its `backend/app/modules/<name>/CHANGELOG.md` updated under `## Unreleased`

## Test plan

<!-- How a reviewer would verify this end-to-end. -->

- [ ]
