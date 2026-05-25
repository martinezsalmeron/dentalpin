# Changelog — periodontogram module

## Unreleased

- feat(indices): `close_snapshot` now computes the SEPA bundle
  (BoP %, PI %, mean CAL, deep-pocket count) over the snapshot's
  sites, persists it on the row as JSONB, and publishes the new
  `periodontogram.snapshot.closed` event for downstream subscribers.
  A new `GET /snapshots/{id}/indices` endpoint serves the frozen
  bundle on closed snapshots and a live-computed bundle on drafts.
- feat(coupling): draft creation reads tooth state from the
  `odontogram` module via `OdontogramService` — missing teeth come
  out as `is_present=False` and performed implants flip
  `is_implant=True` on the seeded perio rows. Read-only; no FK.
- feat(lifecycle): full draft→closed snapshot service +
  `/api/v1/periodontogram/` router. Idempotent draft creation
  pre-seeds 32 permanent teeth, PATCH endpoints support partial
  payloads with closed-state 409 guards, timeline lists closed
  snapshots with site-completeness `change_count`.
- feat(skeleton): initial module skeleton — manifest, models
  (`PeriodontogramSnapshot`, `PeriodontogramTooth`, `PeriodontogramSite`),
  Alembic branch `periodontogram` with `perio_0001_initial`. Empty
  router; service/indices stubs. Optional + removable (`installable=True`,
  `auto_install=False`, `removable=True`). Branch-scoped uninstall test
  added under `backend/tests/test_uninstall_roundtrip.py`.
