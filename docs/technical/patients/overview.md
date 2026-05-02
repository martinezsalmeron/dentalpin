---
module: patients
last_verified_commit: 0e9a0ac
---

# Patients — technical overview

Patient identity: name, contact, demographics, status. Foundational
module — most other modules depend on it. Soft-deleted via `status`,
never hard-deleted.

## Models

- `Patient` — identity row keyed on `(clinic_id, id)`. Status enum
  `{active, archived}`. `do_not_contact` flag is the operational opt-out
  honoured by recalls and any future outreach module.
- `PatientExtended` — denormalised demographics / contact extension
  (1:1 with `Patient`). Loaded lazily; the list endpoint returns the
  base model only.

Source: `backend/app/modules/patients/models.py`.

## Services

`PatientService` (static methods on a class). Routers stay thin; business
logic and event publishing live here.

| Method | Purpose | Emits |
|--------|---------|-------|
| `list(db, clinic_id, page, page_size)` | Paginated list, archived hidden by default. | — |
| `recent(db, clinic_id)` | Sidebar quick-access list. | — |
| `get(db, clinic_id, patient_id)` | Detail lookup. | — |
| `create(db, clinic_id, data)` | Insert + extended row in one tx. | `patient.created` |
| `update(db, clinic_id, patient_id, data)` | Partial update. | `patient.updated` |
| `archive(db, clinic_id, patient_id)` | Soft delete. | `patient.archived` |

Source: `backend/app/modules/patients/service.py`.

## Multi-tenancy

Every query MUST filter by `clinic_id`. There is no public method on
`PatientService` that does not require a `clinic_id` argument — this is
intentional. Future agent tools accessing patients must pass the same
context.

## Frontend

Nuxt layer at `backend/app/modules/patients/frontend/`. Two pages:

- `pages/patients/index.vue` → `/patients` (list). Documented in
  [`user-manual/en/patients/screens/list.md`](../../user-manual/en/patients/screens/list.md).
- `pages/patients/[id].vue` → `/patients/:id` (detail). Documented in
  [`user-manual/en/patients/screens/detail.md`](../../user-manual/en/patients/screens/detail.md).

The detail page exposes the slot `patient.summary.actions` for sibling
modules to inject action buttons (recalls "Set recall", future outreach,
etc.). Slot contract is stable — sibling modules depend on it through the
slot registry, not direct imports.

## Lifecycle

`installable=True`, `auto_install=True`, `removable=False`. Removing the
patients module would orphan most of the system — the foundation never
leaves.

## Related ADRs

- [`0001` — modular plugin architecture](../../adr/0001-modular-plugin-architecture.md)
- [`0003` — event bus over direct imports](../../adr/0003-event-bus-over-direct-imports.md)
- [`0005` — relative permissions](../../adr/0005-relative-permissions.md)

## See also

- [Events](./events.md) — full table of `patient.*` events.
- [Permissions](./permissions.md) — `patients.read`, `patients.write`.
- Module CLAUDE notes: [`backend/app/modules/patients/CLAUDE.md`](../../../backend/app/modules/patients/CLAUDE.md).
