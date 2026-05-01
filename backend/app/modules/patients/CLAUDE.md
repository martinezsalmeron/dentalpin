# Patients module

Patient identity: name, contact, demographics, status. Foundational
module — most other modules depend on it. Soft-deleted via `status`,
never hard-deleted.

## Public API

Routes mounted at `/api/v1/patients/`.

- `GET    /patients`        — list (paginated); `patients.read`
- `GET    /patients/{id}`   — detail; `patients.read`
- `POST   /patients`        — create; `patients.write`
- `PUT    /patients/{id}`   — update; `patients.write`
- `DELETE /patients/{id}`   — soft-archive (status → archived); `patients.write`

## Dependencies

`manifest.depends = []`. Foundational. **Other modules may declare
`depends: ["patients"]`** — keeping this module stable matters for the
whole system.

## Permissions

`patients.read`, `patients.write` (declared relative; registry
namespaces them).

## Events emitted

| Event | When | Payload keys |
|---|---|---|
| `patient.created` | `PatientService.create` succeeds | `patient_id`, `clinic_id` |
| `patient.updated` | `PatientService.update` succeeds | `patient_id`, `changes` |
| `patient.archived` | `PatientService.archive` (soft-delete) | `patient_id` |

See `service.py:113`, `service.py:131`, `service.py:142`.

## Events consumed

None.

## Lifecycle

- `installable=True`, `auto_install=True`, `removable=False` —
  removing patients would orphan most of the system.

## Gotchas

- **Soft delete only.** `DELETE /patients/{id}` flips `status` to
  archived; the row stays. Do not add a hard-delete endpoint.
- **Multi-tenancy.** Every query MUST filter `Patient.clinic_id`.
  This includes future agent tools.
- **No cross-module FKs into patients without `depends: ["patients"]`**
  in the consuming module's manifest.
- **`do_not_contact` flag** — operational opt-out used by recalls and
  any future outreach module. Sibling modules MUST filter
  `Patient.do_not_contact == False` in addition to the
  `Patient.status != "archived"` filter when building call/outreach
  lists.
- **Slot `patient.summary.actions`** — extension point exposed on
  `PatientSummaryHero` for sibling modules to contribute action
  buttons (e.g. recalls "Set recall"). Stable contract — sibling
  modules depend on it via the slot registry, not via imports.

## Related ADRs

- `docs/adr/0001-modular-plugin-architecture.md`
- `docs/adr/0003-event-bus-over-direct-imports.md`
- `docs/adr/0005-relative-permissions.md`

## CHANGELOG

See `./CHANGELOG.md`.
