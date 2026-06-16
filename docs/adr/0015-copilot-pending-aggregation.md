# 0015 — Aggregate the copilot "Pendientes" feed through the tool registry

- **Status:** accepted
- **Date:** 2026-06-15
- **Deciders:** Core team
- **Tags:** copilot, agents, modules, rbac

## Context

The IA redesign (Fase 2, `docs/technical/copilot/ia-redesign-plan.md`)
adds a read-only **Pendientes** feed to the copilot drawer: open work the
caller can act on — overdue recalls, budgets awaiting a response, etc.
The data lives in other modules (`recalls`, `budget`, …). Copilot keeps
`manifest.depends = []` and must not import another module's service
(ADR 0001/0003). The question the roadmap flagged: **how does copilot
aggregate cross-module signals for this feed?**

Three mechanisms were on the table: call the modules' agent **tools**
through the registry; import their **read services** directly; or react to
**events** and maintain a copilot-owned projection table.

## Decision

The Pendientes feed aggregates by calling the **existing agent tools**
through the global `tool_registry`, with an `AgentContext` whose
permissions are `get_role_permissions(caller_role)` — the exact same path
the chat turn and the morning digest already use. No new tables, no
cross-module imports.

Clarifications:

- One reusable per-clinic copilot agent + a single reusable session
  (metadata `surface=copilot_pending`) back the audit context, so a
  drawer open does **not** insert agent/session rows each time.
- RBAC parity is mechanical: the registry enforces each tool's
  `permissions` against the caller's role, so the feed can never surface
  anything the caller couldn't see in the owning module.
- A tool whose module is uninstalled is simply absent from
  `tool_registry.list()` and its section is omitted.

## Consequences

### Good

- `depends = []` holds — copilot stays cleanly removable.
- RBAC parity for free; no second authorization path to keep in sync.
- Consistent with chat + digest — one aggregation pattern in the module.
- Read tool calls land in `agent_audit_logs`, so they show up in the
  `GET /metrics` dashboard like any other usage.

### Bad / accepted trade-offs

- The feed is limited to what tools expose; a new pending source needs a
  tool (which is the right place for it anyway).
- Each pending fetch executes N tool calls inline (currently 2). Bounded
  and fast; if it grows, batch or cache behind the reusable session.
- Sources without a tool yet (cash mismatch, the "Hecho"/done timeline
  filter) are deferred until the relevant tool exists.

## Alternatives considered

- **Import module read services directly** — rejected: breaks the
  `depends = []` contract and duplicates the RBAC checks the tools
  already encapsulate.
- **Event-driven projection table** — rejected for the live feed:
  eventual-consistency and a copilot-owned copy of other modules' state
  add bug surface for a read that the registry serves synchronously.
  (Events remain the right tool for *nudges*, ADR 0014 — a one-shot
  reaction, not a live aggregate.)

## How to verify the rule still holds

- `tests/test_copilot_pending.py` — the endpoint runs and reuses a single
  session across calls.
- `tests/test_module_isolation.py` — copilot declares no `depends` and
  imports no sibling module.
- grep: `PendingService` calls only `tool_registry`, never
  `from app.modules.<other>` .

## References

- `backend/app/modules/copilot/service.py` (`PendingService`)
- `backend/app/modules/copilot/router.py` (`GET /pending`)
- ADR 0001 (modular contract), ADR 0003 (event bus over imports),
  ADR 0014 (proactivity / nudges)
- `docs/technical/copilot/ia-redesign-plan.md` (Fase 2)
