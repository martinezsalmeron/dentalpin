---
module: patients
last_verified_commit: 0e9a0ac
---

# Patients

The patients module manages identity records for the people your clinic
treats: name, contact details, demographics, and lifecycle status.
Almost every other module in DentalPin links back to a patient row.

## Screens

- [Patient list](./screens/list.md) — search, browse, create patients.
- [Patient detail](./screens/detail.md) — single patient view: identity
  card, extended demographics, sibling-module actions (recalls, photos,
  treatment plans, …).

## Quick reference

| Action | Required permission |
|--------|---------------------|
| Browse patients | `patients.read` |
| Create or edit a patient | `patients.write` |
| Archive a patient (soft delete) | `patients.write` |

Patients are never hard-deleted. Archived rows stay in the database for
audit and historical reporting; they're hidden from the default list and
search results.

## Related modules

- **Recalls** — sets the next contact date for a patient. Activates the
  "Set recall" button on the patient detail.
- **Treatment plans** — link plans and budgets to a patient.
- **Media / photos** — attach files and clinical photography to a
  patient (or to entities that belong to a patient).
- **Schedules** — book appointments against a patient.

For end-user instructions, follow the screen-by-screen guides above.
