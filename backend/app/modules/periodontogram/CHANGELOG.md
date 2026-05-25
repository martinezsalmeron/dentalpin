# Changelog — periodontogram module

## Unreleased

- feat(skeleton): initial module skeleton — manifest, models
  (`PeriodontogramSnapshot`, `PeriodontogramTooth`, `PeriodontogramSite`),
  Alembic branch `periodontogram` with `perio_0001_initial`. Empty
  router; service/indices stubs. Optional + removable (`installable=True`,
  `auto_install=False`, `removable=True`). Branch-scoped uninstall test
  added under `backend/tests/test_uninstall_roundtrip.py`.
