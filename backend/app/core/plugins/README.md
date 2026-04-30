# core/plugins

Module discovery, lifecycle, and DB plumbing. Read this when you need to know
which file owns what part of the install/uninstall pipeline.

The full module-author guide lives in
[`docs/technical/creating-modules.md`](../../../../docs/technical/creating-modules.md);
this README is the tour of *core/plugins itself*.

## Files

| File | Role |
|------|------|
| `__init__.py` | Re-exports `BaseModule`, `ModuleContext`. Public surface for module authors. |
| `base.py` | `BaseModule` ABC. The contract every module implements: `manifest`, `get_models`, `get_router`, `get_event_handlers`, `get_permissions`, `get_tools`, `install`/`uninstall`/`post_upgrade` hooks. |
| `context.py` | `ModuleContext` passed to lifecycle hooks (db session, event bus, logger). |
| `manifest.py` | `Manifest` dataclass + `ManifestError`. Lenient parser — only `name` and `version` are required. |
| `manifest_validator.py` | Stricter checks layered on top of `Manifest`: semver format, role names, declared permissions, navigation prefixes, branch isolation when `removable=True`. CI gate. |
| `state.py` | `ModuleState` enum (`uninstalled`/`to_install`/`installed`/…) and `ModuleCategory`. |
| `topology.py` | `topological_sort` helper used by loader, service, and processor for module dependency ordering. |
| `loader.py` | Discovery: entry points (PyPI) + filesystem scan (dev). Mounts routers, subscribes events, registers tools. Single boot-time entry point: `load_modules(app)`. |
| `registry.py` | `module_registry` singleton — in-memory map of name → `BaseModule`. Invalidates the role-permission cache when modules are added. |
| `db_models.py` | `ModuleRecord`, `ModuleOperationLog`, `ExternalId` SQLAlchemy models. The `core_module_*` tables. |
| `service.py` | `ModuleService`: state-transition API (`install`/`uninstall`/`upgrade`) and read views (`list_modules`/`status`/`doctor`). Reconciles disk → DB at boot. |
| `processor.py` | `PendingProcessor`: lifespan executor that runs `to_install`/`to_upgrade`/`to_remove` (migrate → seed → lifecycle hook → finalize, with pg_dump backup before uninstall). |
| `operation_log.py` | `OperationLog` writer + `LogEntry` reader for the `core_module_operation_log` audit trail. |
| `external_id.py` | `ExternalIdHelper` for cross-module logical links without DB-level FKs (preserves uninstall safety). |
| `alembic_paths.py` | Filesystem + Alembic graph helpers shared by `env.py`, the validator, and the service: `discover_version_locations`, `resolve_module_branch_head`, `module_branch_is_isolated`. |
| `yaml_loader.py` | Declarative seed data loader for `manifest.data_files`. |
| `frontend_layers.py` | Discovers `manifest.frontend.layer_path` and writes `frontend/modules.json` so Nuxt picks up community layers. |
| `router.py` | FastAPI router for the module admin API mounted at `/api/v1/modules/`. |

## Reading order

1. `base.py` — what a module looks like.
2. `manifest.py` + `state.py` — the metadata and the lifecycle states.
3. `loader.py` — how modules get discovered and mounted at boot.
4. `service.py` — the API the admin UI calls (state transitions).
5. `processor.py` — what actually runs at lifespan startup to fulfil pending transitions.

Everything else is plumbing those five pieces lean on.
