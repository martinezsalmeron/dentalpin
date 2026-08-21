# Changelog — medical_reference module

## Unreleased

- `get`, `get_interaction`, and `get_contraindication` now filter by
  `clinic_id` in addition to the row's own id. These back every
  update/deactivate endpoint in the module (allergies, medications,
  surgeries, diseases, interactions, contraindications) — previously
  any clinic could rename or deactivate another clinic's reference data
  by guessing/enumerating an id.
- `depends` now declares `patients` explicitly — `router.py` imports
  `patients.service.PatientService` directly, which needs its own
  declared entry regardless of `patients_clinical`'s own transitive
  dependency on it.
- `dentist` now has `write` (was read-only). The frontend's reference
  search already called `create()` when a dentist typed a new allergy
  that wasn't in the list yet — with write restricted to admin, that
  silently 403'd with no fallback. Matches the precedent already set
  by `patients_clinical`'s own role permissions for the same category
  of clinical data.
- Added `CLAUDE.md` and this file (module had neither).
- Added `tests/modules/medical_reference/test_tenant_isolation.py`.

## 0.3.0 (prior)

- Interaction and contraindication tables, plus `get_patient_flags` for
  active per-patient warnings.

## 0.2.0 (prior)

- Surgery reference list.

## 0.1.0 (prior)

- Initial schema: allergy, medication, disease reference lists.
