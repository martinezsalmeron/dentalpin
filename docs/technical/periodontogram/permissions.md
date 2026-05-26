---
module: periodontogram
last_verified_commit: 411343e
---

# Periodontogram — permissions

Returned by `PeriodontogramModule.get_permissions()` (relative names
— the registry namespaces them as `periodontogram.<name>`).

| Permission | Allows | Required by |
|------------|--------|-------------|
| `periodontogram.read` | Listing snapshots, reading the timeline, viewing the active draft or a closed snapshot, and pulling the live or frozen indices bundle. | `GET /patients/{id}/snapshots`, `GET /patients/{id}/timeline`, `GET /patients/{id}/draft`, `GET /snapshots/{id}`, `GET /snapshots/{id}/indices`. |
| `periodontogram.write` | Creating a draft, patching tooth and site rows, closing the snapshot, discarding the draft. | `POST /patients/{id}/draft`, `PATCH /snapshots/{id}/teeth/{tn}`, `PATCH /snapshots/{id}/teeth/{tn}/sites/{code}`, `POST /snapshots/{id}/close`, `DELETE /snapshots/{id}`. |

## Role assignment

Declared in the module manifest
([`backend/app/modules/periodontogram/__init__.py`](../../../backend/app/modules/periodontogram/__init__.py)):

| Role          | Permissions    | Notes |
|---------------|----------------|-------|
| admin         | `*`            | Full control, including future delete/admin permissions. |
| dentist       | `*`            | Records and closes exams; can discard their own drafts. |
| hygienist     | `read`, `write`| Hygienists run periodontal exams in many clinics. |
| assistant     | `read`         | View-only access for chairside support. |
| receptionist  | _none_         | No clinical access. |

See `backend/app/core/auth/permissions.py` for the canonical role
table.

## Adding a new permission

1. Add the relative name to `get_permissions()` in
   `backend/app/modules/periodontogram/__init__.py`.
2. Add it to the role mapping in `manifest.role_permissions` (same
   file) so the appropriate roles can use it on a fresh install.
3. Wire the gate on the endpoint via
   `Depends(require_permission("periodontogram.<name>"))`.
4. Mirror in `frontend/app/config/permissions.ts` under
   `PERMISSIONS.periodontogram.*` so the UI can call
   `usePermissions().can(PERMISSIONS.periodontogram.<name>)`.
5. Add a row to this file with the matching endpoints.
6. Re-run `python backend/scripts/generate_catalogs.py`.
