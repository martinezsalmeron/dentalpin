# 0001 — Modular plugin architecture

- **Status:** accepted
- **Date:** 2026-04-27
- **Tags:** modules, architecture

## Context

DentalPin serves a wide spectrum of dental clinics: solo practices, group
clinics, multi-specialty centers, and country-specific compliance regimes
(e.g. Veri\*Factu in Spain). A monolithic codebase forces every clinic to
carry every feature, makes country-specific compliance code mix with
generic clinical logic, and turns every uninstall into a risky migration.

The product also relies on an open-source community to extend it (BSL
1.1 → Apache 2.0). Third-party developers need a clear, stable contract
for plugging in features without forking the core.

## Decision

Build the system as **independent modules** under
`backend/app/modules/<name>/`, discovered via `pyproject.toml` entry
points (`dentalpin.modules`), each owning its router, models, migrations,
events, permissions, and frontend layer. Inter-module communication is
contract-driven:

- Direct service-to-service imports across modules are **forbidden**
  unless the target is in `manifest.depends`.
- The preferred mechanism for cross-module reactions is the **event
  bus** (see ADR 0003).
- Cross-module FKs are allowed **only** against modules in `depends`;
  CI rejects migrations otherwise.
- Permissions are namespaced by the registry: a module returns
  `resource.action`, the registry prefixes with the module name (see
  ADR 0005).

Each module declares its identity, dependencies, install policy, and
role-permission seeds in a single `manifest` dict on the module class.

## Consequences

### Good

- Clinics install only what they need; uninstall is a real, tested
  operation (see ADR 0002 and `backend/tests/test_uninstall_roundtrip.py`).
- Country-specific compliance lives in its own module (`verifactu`)
  without polluting `billing`.
- Third parties can ship modules as separate Python packages with their
  own entry point.
- Each module is a small, agent-friendly unit of work — agents can be
  briefed on one module without reading the whole codebase.

### Bad / accepted trade-offs

- More boilerplate per feature (manifest, branch label, frontend layer,
  events).
- Event-driven cross-module flows are harder to debug than direct
  function calls; we accept this in exchange for isolation.
- Refactors that span multiple modules need to respect the contract —
  no drive-by reorganizations.

## Alternatives considered

- **Single monolithic FastAPI app.** Rejected: no clean uninstall, no
  third-party extensibility, country-specific code drifts everywhere.
- **Microservices.** Rejected: ops overhead is wrong for a clinic-scale
  product; transactional integrity inside a clinic matters more than
  service-level horizontal scaling.

## How to verify the rule still holds

- `backend/tests/test_module_manifest.py`
- `backend/tests/test_module_manifests_consistency.py`
- `backend/tests/test_manifest_validator.py`
- CI job `manifest-consistency` (`.github/workflows/ci.yml`)

## References

- `docs/creating-modules.md` — module-author contract
- `backend/app/core/plugins/base.py:21` — `BaseModule`
- `backend/app/core/plugins/manifest.py` — manifest schema
- `backend/app/core/plugins/loader.py:159` — `discover_modules`
- `backend/app/core/plugins/registry.py:12` — `ModuleRegistry`
- Root `CLAUDE.md` — "Modular architecture" section
