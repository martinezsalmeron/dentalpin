---
module: patients_clinical
last_verified_commit: 50cce0f
---

# Patients-clinical — events

Per-module slice of [`docs/events-catalog.md`](../../events-catalog.md)
(auto-generated). Update both files when adding or removing events.

## Published

| Event | When | Consumers |
|-------|------|-----------|
| `patient.medical_updated` | A patient's medical history (allergies, conditions, medications) is created or edited | patient_timeline |

Published from `router.py` after the update commits. Payload carries
`clinic_id` and `patient_id`. Note the event name is under the
`patient.*` namespace even though it is emitted by `patients_clinical`,
not `patients`.

## Subscribed

_This module does not subscribe to any events._

## Adding a new event

1. Add the constant to `backend/app/core/events/types.py` (`EventType`).
2. Publish from a service method, **after the DB commit succeeds**.
3. Add the row to the table above.
4. Run `python backend/scripts/generate_catalogs.py` to refresh the
   global catalog.
