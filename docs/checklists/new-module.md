# Checklist: new module

Lookup-optimized version of `docs/creating-modules.md`. Tick each box.
For deeper rationale on any line, follow the link.

## Skeleton

- [ ] `backend/app/modules/<name>/` created with `__init__.py`, `models.py`, `router.py`, `service.py`, `migrations/versions/`
- [ ] Module class subclasses `BaseModule` (`backend/app/core/plugins/base.py`)
- [ ] `manifest = {...}` set as class attribute (see `Manifest` in `backend/app/core/plugins/manifest.py` for the full schema)
- [ ] Entry point registered in `backend/pyproject.toml` under `[project.entry-points."dentalpin.modules"]`
- [ ] `get_models()`, `get_router()`, `get_tools()` implemented (the last is mandatory even if empty — see `BaseModule`)

## Manifest fields

- [ ] `name`, `version` (semver), `summary`, `author`, `license`, `category` (`official` | `community`)
- [ ] `depends` — every module accessed across the boundary must be listed
- [ ] `installable`, `auto_install`, `removable` set deliberately (default optional modules to `auto_install=False`)
- [ ] `role_permissions` — every permission listed must also be returned by `get_permissions()`

## Database

- [ ] `clinic_id` column on every multi-tenant table, indexed
- [ ] UUID primary keys, TIMESTAMPTZ timestamps, JSONB for flexible fields
- [ ] Soft delete via `status` for patient-touching data
- [ ] `clinic_id` filter in **every** query (also inside agent tool handlers)

## Migrations

- [ ] Migrations live in `backend/app/modules/<name>/migrations/versions/`
- [ ] First migration of the module sets `branch_labels = ("<name>",)`
- [ ] No revision threads through another module's chain (uninstall safety, issue #56 — see ADR 0002)
- [ ] Cross-module FKs only against modules in `manifest.depends`
- [ ] `alembic upgrade heads` works clean from base

## Permissions

- [ ] `get_permissions()` returns `["resource.action", ...]` (no module prefix — registry adds it)
- [ ] Endpoints protected with `require_permission("<module>.resource.action")`
- [ ] User-facing permissions added to `frontend/app/config/permissions.ts`

## Events

- [ ] New event types added to `backend/app/core/events/types.py` `EventType`
- [ ] Subscribers registered via `get_event_handlers()`
- [ ] No direct imports of services from modules outside `depends` — use the event bus (ADR 0003)

## Frontend layer

- [ ] `backend/app/modules/<name>/frontend/` exists with `nuxt.config.ts`, `pages/`, `components/`
- [ ] `manifest["frontend"]["layer_path"] = "frontend"`
- [ ] Navigation entries declared in `manifest["frontend"]["navigation"]` with namespaced `permission`

## Tests

- [ ] Unit + integration tests under `backend/tests/`
- [ ] If `removable=True`: round-trip uninstall test (see `backend/tests/test_uninstall_roundtrip.py`)
- [ ] `python -m pytest -v` green; manifest-consistency tests still pass

## Docs

- [ ] `backend/app/modules/<name>/CLAUDE.md` written from `docs/checklists/module-claude-template.md`
- [ ] `backend/app/modules/<name>/CHANGELOG.md` started with `## Unreleased`
- [ ] `python backend/scripts/generate_catalogs.py` re-run; `docs/modules-catalog.md` and `docs/events-catalog.md` committed
- [ ] If a new domain term: appended to `docs/glossary.md`
- [ ] If an architectural decision was made: ADR added under `docs/adr/NNNN-title.md`

## Reference modules to copy from

- **Foundational, simple, non-removable** → `backend/app/modules/patients/`
- **Removable, isolation-critical** → `backend/app/modules/schedules/` (issue #39)
- **Heavy `depends`, event-driven** → `backend/app/modules/treatment_plan/`
- **Compliance/integration with external system** → `backend/app/modules/verifactu/`
