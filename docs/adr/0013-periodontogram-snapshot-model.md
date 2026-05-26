# 0013 — Periodontogram snapshots are immutable dated rows, not an event stream

- **Status:** accepted
- **Date:** 2026-05-26
- **Deciders:** Ramon Martinez (product), Claude (engineering)
- **Tags:** modules, periodontogram, data-model

## Context

The `periodontogram` module (issue #79) records SEPA periodontal exams
for a patient. The existing `odontogram` module persists state changes
as an **event-sourced history** (`odontogram_history`) and reconstructs
a tooth's state at any past date by replaying entries; this works
well for "what was tooth 36 in March?" queries.

Periodontal exams are different. A clinician interprets a single
exam as one **act in time**: the dentist sits with the patient,
records nine metrics on every tooth and six sites, then signs the
session off. Comparing evolution means comparing two full exams,
not reconstructing intermediate states between them. There is no
clinical meaning to "the periodontogram between session A and B".

Two viable persistence shapes were on the table for PR-1:

1. Mirror the odontogram — one row per metric change, reconstruct on
   demand.
2. Treat each exam as an immutable dated snapshot — three relational
   tables (`periodontogram_snapshots`, `periodontogram_teeth`,
   `periodontogram_sites`) with a `status` field and a draft → closed
   transition.

## Decision

Adopt the **snapshot model**: each exam owns one
`periodontogram_snapshots` row with `status ∈ {draft, closed}`. A
partial unique index enforces "at most one draft per patient"
(`uq_perio_snap_one_draft_per_patient`). Closing the snapshot freezes
it (DB CHECK rejects mutations on closed rows via 409 in the API)
and persists the computed SEPA indices (BoP %, PI %, mean CAL,
deep-pocket count) as JSONB on the same row.

## Consequences

### Good

- **One slider node = one real exam.** The timeline UI navigates
  closed snapshots directly; no reconstruction needed.
- **Cheap analytics.** Aggregates over indices are O(snapshots),
  not O(events). The `indices` JSONB blob lets the indices banner
  render without touching the sites table.
- **Simpler tests.** Lifecycle invariants (one draft, immutability
  after close) live as database constraints + service-layer checks;
  no replay logic to assert against.
- **Audit by design.** A closed snapshot is a frozen artifact;
  re-opening is intentionally disallowed in MVP. Corrections mean
  a new exam, which mirrors clinical reality.

### Bad / accepted trade-offs

- **No intermediate states.** "Show me probing depth on 16-MV
  yesterday" only makes sense if there was an exam yesterday. We
  cannot reconstruct between sessions. Accepted — clinicians don't
  ask this question.
- **Three tables instead of one history table.** Slightly more DDL
  churn on first install, three migrations to coordinate on
  schema evolution. Mitigated by the module owning its own Alembic
  branch (`branch_labels=("periodontogram",)`).
- **Closed snapshots cannot be edited.** If the dentist fat-fingers
  the close action, the workflow is "open new draft, copy values,
  close again". Acceptable for MVP; "reopen" can be added later
  behind admin-only permission.

## Alternatives considered

- **Event-sourced history like odontogram** — Rejected because the
  unit of clinical interpretation is the whole exam, not the single
  metric. Replay cost (>200 events per exam × N exams) outweighs
  the flexibility nobody asked for.
- **JSONB document per snapshot** — Rejected because analytical
  queries (mean CAL, deep-pocket count, comparing two sessions
  site-by-site) become painful and index-unfriendly. Three normalised
  tables let Postgres do the heavy lifting.
- **Single table with `snapshot_id` denormalised** — A wider
  composite-key fact table. Rejected because the three-level hierarchy
  (snapshot → tooth → site) is intrinsically nested; embedding the
  hierarchy in primary keys hurts UPSERT semantics on partial
  per-site edits.

## How to verify the rule still holds

- `backend/tests/test_uninstall_roundtrip.py::test_periodontogram_uninstall_roundtrip_is_branch_scoped`
  drops + reinstalls only the three snapshot tables; if someone
  smuggles in an event-log table for perio, this test fails.
- `backend/tests/modules/periodontogram/test_snapshot_lifecycle.py::test_patch_tooth_and_site_then_close_freezes_state`
  asserts 409 on writes after close. Removing the immutability
  invariant breaks the assertion.
- DB constraint `uq_perio_snap_one_draft_per_patient` (partial
  unique index) enforces "one draft per patient". Migration drift
  would surface in `alembic check`.

## References

- Plan: `docs/technical/periodontogram-plan.md`
- Module code: `backend/app/modules/periodontogram/`
- Issue #79
- Related: ADR 0001 (modular plugin architecture), ADR 0002
  (per-module Alembic branches).
