# 0005 — Relative permissions, registry-prefixed namespacing

- **Status:** accepted
- **Date:** 2026-04-27
- **Tags:** modules, rbac, security

## Context

Modules need their own permissions (`patients.read`, `billing.write`).
If every module hardcodes the namespace itself, two failure modes
appear:

1. A community module picks a name that collides with another's
   (`patients.read` already exists in `patients`; another module uses
   the same string and silently grants access).
2. Refactoring a module's name (rename, fork) breaks every grant string
   it ever wrote.

We want the module's permission identity to come from one place: its
`name` in the manifest, used both for routing and for permission
namespacing.

## Decision

Modules return permissions in **relative form** from
`get_permissions()`:

```python
def get_permissions(self) -> list[str]:
    return ["patients.read", "patients.write"]   # no module prefix
```

The `ModuleRegistry` (`backend/app/core/plugins/registry.py:40`)
namespaces them at load time:

```python
permissions.append(f"{module.name}.{perm}")
```

The same convention applies to `manifest.role_permissions` (relative
strings, registry namespaces them when expanding into the
`ROLE_PERMISSIONS` table) and to navigation entries
(`manifest.frontend.navigation[].permission` — must already be
namespaced because it's consumed by the frontend, which has no registry
to prefix it for free; `manifest_validator.py` enforces this).

`*` and `<resource>.*` wildcards are honored at the role layer; the
manifest validator enforces that any non-wildcard permission listed in
`role_permissions` is actually returned by `get_permissions()`.

## Consequences

### Good

- Permission strings outside a module are always
  `<module>.<resource>.<action>` — no collisions, no rename
  hand-cranking.
- Refactoring a module's name only touches the manifest; the registry
  re-namespaces the rest.
- Frontend permission constants (`frontend/app/config/permissions.ts`)
  stay in sync with backend by reading the namespaced output of the
  registry.

### Bad / accepted trade-offs

- Module authors must remember not to prefix; CI catches the wrong case
  via `test_manifest_validator.py`.
- Frontend `navigation[].permission` must be namespaced manually because
  the manifest is shipped as data, not run through the registry on the
  client.

## Alternatives considered

- **Hardcoded namespaces in every module.** Rejected — see Context.
- **Single global permissions table.** Rejected — defeats module
  isolation and forbids community modules from declaring their own.

## How to verify the rule still holds

- `backend/tests/test_manifest_validator.py` — UNKNOWN_PERMISSION,
  NAV_PERM_NOT_NAMESPACED checks
- `backend/app/core/plugins/manifest_validator.py:86`
- `backend/app/core/plugins/registry.py:40` — `get_all_permissions`

## References

- `backend/app/core/auth/permissions.py` — `ROLE_PERMISSIONS`,
  `has_permission`
- `backend/app/core/auth/dependencies.py` — `require_permission`
- Root `CLAUDE.md` — "RBAC" section
