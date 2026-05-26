---
module: periodontogram
screen: view
route: /patients/{id}?clinicalMode=diagnosis&diagnosisView=periodontogram
related_endpoints:
  - GET /api/v1/periodontogram/patients/{patient_id}/snapshots
  - GET /api/v1/periodontogram/patients/{patient_id}/timeline
  - GET /api/v1/periodontogram/patients/{patient_id}/draft
  - POST /api/v1/periodontogram/patients/{patient_id}/draft
  - GET /api/v1/periodontogram/snapshots/{snapshot_id}
  - GET /api/v1/periodontogram/snapshots/{snapshot_id}/indices
  - PATCH /api/v1/periodontogram/snapshots/{snapshot_id}/teeth/{tooth_number}
  - PATCH /api/v1/periodontogram/snapshots/{snapshot_id}/teeth/{tn}/sites/{site_code}
  - POST /api/v1/periodontogram/snapshots/{snapshot_id}/close
  - DELETE /api/v1/periodontogram/snapshots/{snapshot_id}
related_permissions:
  - periodontogram.read
  - periodontogram.write
related_paths:
  - backend/app/modules/periodontogram/frontend/components/PeriodontogramView.vue
  - backend/app/modules/periodontogram/frontend/components/PeriodontogramChart.vue
  - backend/app/modules/periodontogram/router.py
last_verified_commit: 411343e
---

# Periodontogram view

The **Periodontogram** sub-tab lives inside *Patient → Clinical →
Diagnosis*. It bundles the timeline slider, the indices banner, and
the SEPA-style chart for both arches.

## At a glance

```
┌────────────────────────────────────────────────────────────────────┐
│ [Amber banner — only when viewing a past snapshot] .............. │
│                                                                    │
│ [Date slider]──●──────●──●─────────[Now]                           │
│                                                                    │
│ ┌────────────────────────────────────────────────────────────────┐ │
│ │ [Pill] Draft / Closed · 23 Mar 2026                            │ │
│ │ BoP 18%  ·  PI 12%  ·  CAL 1.8mm  ·  Pockets ≥5mm: 3           │ │
│ └────────────────────────────────────────────────────────────────┘ │
│                                                                    │
│ UPPER                                                              │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  SEPA table (9 rows × 16 teeth)                               │ │
│  │  Teeth — buccal face                                          │ │
│  │  Teeth — palatal face (vertical flip)                         │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│ LOWER                                                              │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Teeth — lingual face (vertical flip)                         │ │
│  │  Teeth — buccal face                                          │ │
│  │  SEPA table                                                   │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│ [Sticky bottom bar — drafts only]                                  │
│  [⏳ Saved]      [Discard draft]    [Close session ✓]              │
└────────────────────────────────────────────────────────────────────┘
```

## Empty state

If the patient has no snapshots and no active draft, the sub-tab
shows a card with a **Start exam** button. Clicking it creates a
pre-filled draft and loads the full view.

## Cell-level editing

1. **Site (probing, margin, bleeding, plaque, suppuration).** Click
   any dot on a tooth or any sub-cell on the *Bleeding / Plaque /
   Gingival margin / Probing* rows. A modal opens with five fields.
2. **Tooth (mobility, prognosis, furcation, keratinized gingiva).**
   Click on the matching row for the tooth. A modal opens with the
   per-tooth fields. Furcation rows only appear for molars.

Edits autosave after a 600 ms debounce window. The indicator at the
bottom-left of the chart shows the state: *Saving…* / *Pending
changes* / *Saved*.

## Visual heatmap

Probing depth colours each dot:

| Probing | Colour |
|---------|--------|
| 0–3 mm | Green |
| 4 mm | Yellow |
| 5–6 mm | Orange |
| ≥ 7 mm | Red |

Bleeding and plaque add small overlay markers on the dot (red and
blue respectively).

## History

The top slider is the same component used by the odontogram: each
node is a closed snapshot. Selecting a past date raises an amber
banner and disables every input. *Return to current* reloads the
most recent snapshot or the active draft.

## Close session

From the sticky bottom bar, *Close session* opens a confirmation
modal with an optional clinical note field. On confirm:

1. Pending in-flight edits are flushed to the backend.
2. The SEPA indices are computed and frozen on the snapshot.
3. The snapshot status flips to `closed`, the slider gains a new
   node, and every input becomes read-only.

## Discard draft

*Discard draft* deletes every value entered into the active draft.
It is not reversible — the modal warns before confirming.
