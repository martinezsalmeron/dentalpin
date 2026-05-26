---
module: periodontogram
last_verified_commit: 411343e
---

# Periodontogram — events

Per-module slice of [`docs/events-catalog.md`](../../events-catalog.md)
(auto-generated). Update both files when adding or removing events.

## Published

| Event | When | Payload |
|-------|------|---------|
| `periodontogram.snapshot.closed` | A draft transitions to `closed` via `POST /snapshots/{id}/close`. Fires after `snapshot.indices` is computed + persisted, inside the same DB session as the status flip. | `snapshot_id`, `patient_id`, `clinic_id`, `closed_at`, `closed_by`, `indices` (JSONB blob with `bop_pct`, `pi_pct`, `cal_mean_mm`, `deep_pockets_count`). |

The event is **fire-and-forget**: subscribers (currently none —
patient_timeline integration is queued) react asynchronously. The
publish call is inside `PeriodontogramService.close_snapshot`
([`backend/app/modules/periodontogram/service.py`](../../../backend/app/modules/periodontogram/service.py)).

## Subscribed

| Event | Handler | Effect |
|-------|---------|--------|
| `odontogram.treatment.performed` | `events.on_odontogram_treatment_performed` | Logging-only stub today. The hook stays in place so a future iteration can refresh the active draft's `is_present` / `is_implant` flags when the odontograma records an implant, extraction or crown. |
| `patient.archived` | `events.on_patient_archived` | Logging-only stub today. A future iteration will discard active drafts owned by the archived patient. The partial unique index already protects against new drafts being attached to an archived patient. |

## Why `periodontogram` does not publish per-edit events

Per ADR 0013, exams are interpreted as a whole. A `snapshot.closed`
event is enough for downstream timelines; we deliberately do NOT
publish `periodontogram.tooth.updated` or
`periodontogram.site.updated` to avoid encouraging consumers to
react to in-progress drafts.

## Adding a new event

1. Add the constant to `backend/app/core/events/types.py` (`EventType`)
   if a new event type is required.
2. Publish from a service method, after the DB commit succeeds.
3. Add a row to the table above.
4. Run `python backend/scripts/generate_catalogs.py` to refresh the
   global catalog.
