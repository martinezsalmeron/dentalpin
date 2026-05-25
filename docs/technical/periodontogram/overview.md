---
module: periodontogram
last_verified_commit: 452a17e
---

# Periodontogram — technical overview

SEPA-standard periodontal charting. Dated snapshots, six probing sites
per tooth, computed BoP / PI / CAL indices on close. Optional and
removable.

Source of truth for the design: [`docs/technical/periodontogram-plan.md`](../periodontogram-plan.md).

## Scope

- Pre-fills tooth state (`is_present`, `is_implant`) from the patient's
  current `odontogram` snapshot at draft creation.
- Captures six probing sites per tooth: PD (pocket depth), CAL
  (clinical attachment loss), recession, BoP, plaque, suppuration,
  mobility, furcation, MGJ.
- On `close`, computes per-snapshot summary indices (BoP%, PI%,
  PD/CAL distribution, mean PD/CAL). Stored alongside the snapshot.
- Pre-fills the patient odontogram with implant-suggestion flags
  derived from snapshot deltas (`odontogram.treatment.performed`
  publishes back).

## API surface

Mounted at `/api/v1/periodontogram/`.

- `GET    /patients/{id}/snapshots` — list snapshots.
- `GET    /patients/{id}/timeline` — chronological index series.
- `GET    /patients/{id}/draft` — current draft (one per patient).
- `POST   /patients/{id}/draft` — create a draft. Pre-fills from
  odontogram.
- `GET    /snapshots/{id}` — full snapshot.
- `PATCH  /snapshots/{id}/teeth/{tn}` — per-tooth fields.
- `PATCH  /snapshots/{id}/teeth/{tn}/sites/{site}` — per-site fields.
- `POST   /snapshots/{id}/close` — finalise + compute indices.
- `DELETE /snapshots/{id}` — drafts only.
- `GET    /snapshots/{id}/indices` — read-only computed indices.

## Frontend

Nuxt layer at `backend/app/modules/periodontogram/frontend/`. Renders
inside the clinical record under the **Diagnosis** sub-tab via the
`patients_clinical.diagnosis.subtab` slot. No standalone pages.

## Storage

- One row per snapshot. Status `draft` or `closed`.
- `teeth: jsonb` — keyed by `1..32`, holds per-tooth flags + the six
  sites' arrays.
- `indices: jsonb` — computed once, on close. Frozen.

## Lifecycle

- `installable=True`, `auto_install=False`, `removable=True`.
- Round-trip uninstall covered in
  `backend/tests/test_uninstall_roundtrip.py`.
- No FKs into other modules — uninstall drops the `periodontogram_*`
  tables without cascading.

## Dependencies

`manifest.depends = ["patients", "odontogram"]`. Odontogram is read
only at draft creation; coupling is one-way via the event bus
afterwards.

## Related ADRs

- [`docs/adr/0001-modular-plugin-architecture.md`](../../adr/0001-modular-plugin-architecture.md)
- [`docs/adr/0002-per-module-alembic-branches.md`](../../adr/0002-per-module-alembic-branches.md)
- [`docs/adr/0003-event-bus-over-direct-imports.md`](../../adr/0003-event-bus-over-direct-imports.md)
