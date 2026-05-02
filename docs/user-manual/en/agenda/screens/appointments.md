---
module: agenda
screen: list
route: /appointments
related_endpoints:
  - DELETE /api/v1/agenda/appointments/{appointment_id}
  - DELETE /api/v1/agenda/cabinets/{cabinet_id}
  - GET /api/v1/agenda/appointments
  - GET /api/v1/agenda/appointments/{appointment_id}
  - GET /api/v1/agenda/appointments/{appointment_id}/cabinet-history
  - GET /api/v1/agenda/appointments/{appointment_id}/transitions
  - GET /api/v1/agenda/cabinets
  - GET /api/v1/agenda/kanban/day
  - PATCH /api/v1/agenda/appointment-treatments/{appointment_treatment_id}
  - PATCH /api/v1/agenda/appointments/{appointment_id}/cabinet
  - POST /api/v1/agenda/appointments
  - POST /api/v1/agenda/appointments/{appointment_id}/transitions
  - POST /api/v1/agenda/cabinets
  - PUT /api/v1/agenda/appointments/{appointment_id}
  - PUT /api/v1/agenda/cabinets/{cabinet_id}
related_permissions:
  - agenda.appointments.read
  - agenda.appointments.write
  - agenda.cabinets.read
  - agenda.cabinets.write
related_paths:
  - backend/app/modules/agenda/frontend/pages/appointments/index.vue
last_verified_commit: 0000000
---

# /appointments

> _Scaffolded stub — replace with proper documentation when this module is next touched._

_Screen `/appointments` of the `agenda` module._

## Permissions

- `agenda.appointments.read`
- `agenda.appointments.write`
- `agenda.cabinets.read`
- `agenda.cabinets.write`

## What this screen does

_Documentation pending._

