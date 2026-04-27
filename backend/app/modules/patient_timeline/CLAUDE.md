# Patient timeline module

Unified per-patient activity log. The **firehose subscriber** — listens
to ~22 events across the system to build a single chronological feed.

## Public API

Routes mounted at `/api/v1/patient-timeline/`.

## Dependencies

`manifest.depends = ["patients"]`. Despite consuming events from many
modules, the only **hard** dependency is `patients` (the entity it
indexes). Other event sources are runtime-optional — when a producing
module is uninstalled, this module simply stops receiving its events.

## Permissions

`patient_timeline.read`.

## Events emitted

None.

## Events consumed

22 events: appointment lifecycle, budget lifecycle, invoice lifecycle,
treatment_plan lifecycle, odontogram, documents, email, medical
updates. See `docs/events-catalog.md` for the full list.

## Lifecycle

- `removable=False` today, but a strong candidate for `removable=True`
  in the future — the module is purely a derived view.

## Gotchas

- **Append-only.** Timeline entries are never edited or deleted, only
  archived. Reactions to delete events log a "removed" entry rather
  than deleting the original.
- **Event handlers must be cheap and idempotent.** The same event can
  arrive twice; deduplicate by `(event_type, source_id)`.
- **No upstream coupling.** Don't import any of the producing modules'
  services. The whole point of this module is that it's loosely
  coupled to everyone.

## Related ADRs

- `docs/adr/0001-modular-plugin-architecture.md`
- `docs/adr/0003-event-bus-over-direct-imports.md` — the canonical
  example of the event bus paying off.

## CHANGELOG

See `./CHANGELOG.md`.
