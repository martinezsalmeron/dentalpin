---
module: schedules
last_verified_commit: 0e9a0ac
---

# Schedules — permissions

Returned by `SchedulesModule.get_permissions()` (relative names; the
permission registry namespaces them as `schedules.<name>`).

| Permission | Allows | Required by |
|------------|--------|-------------|
| `clinic_hours.read` | Read clinic-wide hours and overrides. | `GET /api/v1/schedules/clinic-hours`, `GET /api/v1/schedules/clinic-overrides` |
| `clinic_hours.write` | Modify clinic hours and create / edit / delete clinic overrides. | `PUT /api/v1/schedules/clinic-hours`, `POST/PUT/DELETE /api/v1/schedules/clinic-overrides[...]` |
| `professional.read` | Read **any** professional's hours and overrides. | `GET /api/v1/schedules/professionals/{user_id}/hours`, `GET .../overrides` |
| `professional.write` | Modify **any** professional's hours/overrides. | `PUT /api/v1/schedules/professionals/{user_id}/hours`, `POST/PUT/DELETE .../overrides[...]` |
| `professional.own.read` | Read **own** hours/overrides only. Endpoints accept either this or `professional.read`. | Same endpoints, when `user_id == self`. |
| `professional.own.write` | Modify **own** hours/overrides only. | Same endpoints, when `user_id == self`. |
| `availability.read` | Resolve bookable slots for a (date, professional). | `GET /api/v1/schedules/availability` |
| `analytics.read` | Read occupancy / utilisation / peak-hours analytics. | `GET /api/v1/schedules/analytics/*` |

## Role assignment

Default role mappings (in `backend/app/core/auth/permissions.py`):

| Role | Schedules access |
|------|------------------|
| `admin` | All (via `*`). |
| `dentist` | `professional.own.{read,write}`, `availability.read`. Reads but does not write clinic-wide hours. |
| `hygienist` | `professional.own.{read,write}`, `availability.read`. **No analytics.** |
| `assistant` | `professional.own.{read,write}`, `availability.read`. |
| `receptionist` | All read; no `professional.write`; **analytics.read** for occupancy reports. |

Receptionists read analytics; hygienists do not. Don't widen this.

## Adding a new permission

1. Add the relative name to `get_permissions()` in
   `backend/app/modules/schedules/__init__.py`.
2. Add the namespaced form to the relevant role(s) in
   `backend/app/core/auth/permissions.py`.
3. Add a row to the table above.
4. Annotate the endpoint(s) with `Depends(require_permission(...))`.
5. Update `frontend/app/config/permissions.ts` if it gates UI.
