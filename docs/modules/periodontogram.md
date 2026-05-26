# Periodontogram — module deep-dive

> Optional, removable module that adds **SEPA periodontal charting**
> to the patient clinical record. Lives as a sub-tab inside the
> Diagnosis mode of `ClinicalTab`, alongside the odontogram.

| Item | Value |
|------|-------|
| Manifest name | `periodontogram` |
| Version | 0.1.0 |
| Category | official |
| Depends on | `patients`, `odontogram` |
| Installable | yes |
| Auto-installs | no — activate manually from the admin UI |
| Removable | yes (Alembic branch `periodontogram` is isolated) |

Plan + ADR + technical reference:

- [`docs/technical/periodontogram-plan.md`](../technical/periodontogram-plan.md)
- [`docs/technical/periodontogram/overview.md`](../technical/periodontogram/overview.md)
- [`docs/technical/periodontogram/events.md`](../technical/periodontogram/events.md)
- [`docs/technical/periodontogram/permissions.md`](../technical/periodontogram/permissions.md)
- [`docs/adr/0013-periodontogram-snapshot-model.md`](../adr/0013-periodontogram-snapshot-model.md)

## What it does

- Captures the nine SEPA per-tooth metrics — implant flag, mobility,
  prognosis, furcation (buccal + lingual roots, molars only),
  keratinized gingiva width — across the permanent dentition.
- Captures six probing sites per tooth (MV, V, DV, ML, L, DL) with
  probing depth, gingival margin, bleeding, plaque and suppuration.
- Computes the four canonical SEPA indices on close (BoP %, PI %,
  mean CAL, deep-pocket count) and freezes them on the snapshot as
  JSONB.
- Persists each exam as an immutable dated snapshot; at most one
  draft per patient at a time.

## What it does not do

- It does not edit closed snapshots — corrections require a new
  exam (ADR 0013).
- It does not chart deciduous teeth (FDI 51–85). Permanent dentition
  only.
- It does not own clinical notes — the snapshot has a single `notes`
  TEXT column. Multi-note timelines would land in a follow-up that
  extends `clinical_notes` (currently `removable=False`).
- It does not write back to the odontogram. Coupling is one-way
  read at draft creation.

## Install / uninstall

```bash
# install (after activation from the admin UI):
alembic upgrade periodontogram@head

# uninstall (drops the three tables in this module's Alembic branch):
alembic downgrade periodontogram@-1
```

Round-trip cleanliness is asserted in
`backend/tests/test_uninstall_roundtrip.py::test_periodontogram_uninstall_roundtrip_is_branch_scoped`.

## Frontend integration

Periodontogram registers a single slot entry under
`patient.diagnosis.subtabs`. The host (`patients` module's
`DiagnosisModeContainer.vue`) renders the existing `<DiagnosisMode>`
verbatim when the slot is empty — uninstalling the module restores
the pre-slot UI without churn.

UI walkthroughs in Spanish and English live under
[`docs/user-manual/es/periodontogram/`](../user-manual/es/periodontogram/index.md)
and [`docs/user-manual/en/periodontogram/`](../user-manual/en/periodontogram/index.md).
