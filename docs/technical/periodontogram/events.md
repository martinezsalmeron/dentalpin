---
module: periodontogram
last_verified_commit: 452a17e
---

# Periodontogram — events

Per-module slice of [`docs/events-catalog.md`](../../events-catalog.md)
(auto-generated). Update both files when adding or removing events.

## Published

| Event | Source | When | Payload |
|-------|--------|------|---------|
| `periodontogram.snapshot.closed` | `service.py:PeriodontogramService.close` | After indices are computed and the snapshot row is committed with `status='closed'`. | `snapshot_id` (UUID), `patient_id` (UUID), `clinic_id` (UUID), `closed_at` (ISO datetime) |

## Subscribed

| Event | Handler | Why |
|-------|---------|-----|
| `odontogram.treatment.performed` | `events.py:on_odontogram_treatment_performed` | When the odontogram marks a tooth's treatment as performed (e.g. extraction, implant placement), invalidate or annotate the matching draft so the next snapshot reflects the new tooth state. |
| `patient.archived` | `events.py:on_patient_archived` | Soft-delete every snapshot / draft belonging to the archived patient (cascade-by-event, no FK). |

## Adding a new event

1. Add the constant to `backend/app/core/events/types.py` (`EventType`)
   if a new event type is required.
2. Publish from a service method, after the DB commit succeeds.
3. Add a row to the table above.
4. Run `python backend/scripts/generate_catalogs.py` to refresh the
   global catalog.
