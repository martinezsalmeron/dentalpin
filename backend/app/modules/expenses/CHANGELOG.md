# Changelog — expenses module

## Unreleased

- `auto_install` flipped to `False`: optional modules ship inactive and
  the admin activates them from the module admin UI (repo policy, per
  `patient_relationships`/`recall_reminders`/`contacts`).
- Fixed API conventions: `POST /expenses` now returns `201 Created`
  (was defaulting to `200`); `DELETE /expenses/{id}` now returns `204
  No Content` with no body (was `200` wrapping `ApiResponse(data=None)`).
  Updated the frontend's `remove()` to match — it now returns `void`
  instead of expecting a JSON body that no longer exists.
- Added `pt` and `ta` locales (all five UI locales, per the i18n
  checklist — the module previously only had en/es/fr).
- Fixed `"author": "Clinic Custom"` → `"DentalPin Core Team"`, matching
  the convention used by every module in the real repo.
- Added `PERMISSIONS.expenses` to the shared frontend config — the page
  already referenced `PERMISSIONS.expenses.read`/`.write`, the key
  just didn't exist yet.
- Added the round-trip uninstall test required for `removable=True`
  modules (`test_uninstall_roundtrip.py`, `alembic_roundtrip` marker) —
  confirmed it actually catches a regression, not just a tautology, by
  reverting the branch-scoped downgrade target and watching it fail
  before restoring it.
- Added `tests/modules/expenses/test_expenses.py`: happy-path CRUD
  (including the monthly-totals aggregation), and a tenant-isolation
  test. Module had zero test coverage before this.
- Added `docs/technical/expenses/{overview,permissions}.md` (no
  `events.md` — the module emits/consumes none) and bilingual (en/es)
  user-manual screen docs for `/expenses`. Regenerated
  `docs/modules-catalog.md`.
- Every query was already correctly `clinic_id`-scoped — verified
  directly, nothing to fix on the tenancy front.

## 0.1.0 (prior)

- Initial version: fixed office expense CRUD, category filter, monthly
  totals-by-category summary, EN/ES/FR translations.
