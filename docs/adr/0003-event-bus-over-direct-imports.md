# 0003 — Event bus over direct cross-module imports

- **Status:** accepted
- **Date:** 2026-04-27
- **Tags:** modules, events, isolation

## Context

Modules react to each other constantly: `notifications` reacts to
`appointment.scheduled`, `verifactu` reacts to `invoice.issued`,
`patient_timeline` reacts to almost everything. The naive solution —
import the upstream module's service and call it directly — hard-couples
two modules and silently violates `manifest.depends`.

Once two modules import each other's internals, an uninstall is no
longer safe: removing the upstream module breaks the downstream one at
import time, and the dependency is invisible to the loader.

## Decision

Cross-module reactions go through the in-process **event bus**
(`backend/app/core/events/`). Concretely:

- The producing module declares an event name in
  `backend/app/core/events/types.py` (`EventType.ENTITY_ACTION`,
  string `"entity.action"`).
- It calls `event_bus.publish("entity.action", payload)` at the
  transaction boundary in its service.
- Subscribing modules return `{event_name: handler}` from
  `get_event_handlers()`.
- The loader wires subscriptions during `_mount_modules`.

Direct service-to-service imports across modules are forbidden unless
the target is listed in `manifest.depends` *and* the call is part of a
synchronous read (e.g. `budget` reads from `catalog`). Even then, prefer
events for write-side reactions.

## Consequences

### Good

- Producers don't know who consumes them — uninstalling a consumer is
  trivial.
- The events catalog (`docs/events-catalog.md`) becomes a real
  integration map agents can read.
- Tests can subscribe to events to assert behaviour without coupling to
  the consumer.

### Bad / accepted trade-offs

- Reactions are implicit; an agent that grep-traces a function call
  won't see them. The events catalog plus per-module CLAUDE.md
  (publishers + consumers sections) compensate.
- Payloads are dicts, not typed schemas — drift is possible. We accept
  it for now and document payload shapes in the publisher's CLAUDE.md.
- In-process only: no cross-process delivery. Acceptable until we split
  workers; if we do, this ADR will be revisited.

## Alternatives considered

- **Direct imports across modules.** Rejected — see Context.
- **External message broker (Redis Streams, RabbitMQ).** Rejected for
  now: ops overhead doesn't fit a clinic-scale single-process backend.
- **Function-call dispatch via a registry.** Rejected: still requires
  the producer to know the consumer interface.

## How to verify the rule still holds

- Grep `event_bus.publish` to find all publishers. Catalog generator
  (`backend/scripts/generate_catalogs.py`) does this.
- Grep imports from `app.modules.<other>` inside a module — should only
  hit modules in its `depends`.
- `EventType` enum in `backend/app/core/events/types.py` is the
  authoritative list of event names; new events MUST be added here.

## References

- `backend/app/core/events/types.py` — `EventType` enum (34 events)
- `backend/app/core/events/__init__.py` — `event_bus`
- `backend/app/modules/patients/service.py:113` — example publisher
  (`patient.created`)
- `backend/app/modules/notifications/handlers.py` — example subscriber
- `docs/diagrams/event-bus.md`
