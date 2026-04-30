# Technical

Cross-cutting technical reference and implementation plans. Audience: engineers and AI agents extending the platform.

## What lives here

- Cross-cutting concerns: auth, events, RBAC, API conventions, error handling, testing infrastructure.
- The module-author guide ([`creating-modules.md`](./creating-modules.md)) and core API reference ([`core-api.md`](./core-api.md)).
- Technical plans for features in flight (paired with a UX brief in `../features/` when applicable).
- System-wide architecture notes that don't fit a single ADR.

## What does NOT belong here

- Decisions that codify a binding rule → [`../adr/`](../adr/) (point at the relevant tech doc from the ADR).
- Documentation scoped to a single module → [`../modules/`](../modules/).
- Product / UX framing — *what* and *why* → [`../features/`](../features/).

## Style

- Code-first. Show the contract (function signature, payload shape, route), then explain.
- Cite source files as `path:line` so the reader can jump.
- Mark status when a doc describes future work: `status: proposed` / `accepted` / `superseded`.
- When a tech plan ships and the implementation diverges, update the doc or supersede it with an ADR — don't let plans rot.
