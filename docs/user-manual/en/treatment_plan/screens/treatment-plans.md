---
module: treatment_plan
screen: list
route: /treatment-plans
related_endpoints:
  - DELETE /api/v1/treatment_plan/treatment-plans/{plan_id}
  - DELETE /api/v1/treatment_plan/treatment-plans/{plan_id}/items/{item_id}
  - GET /api/v1/treatment_plan/treatment-plans
  - GET /api/v1/treatment_plan/treatment-plans/patient/{patient_id}
  - GET /api/v1/treatment_plan/treatment-plans/pipeline
  - GET /api/v1/treatment_plan/treatment-plans/{plan_id}
  - PATCH /api/v1/treatment_plan/treatment-plans/{plan_id}/items/reorder
  - PATCH /api/v1/treatment_plan/treatment-plans/{plan_id}/items/{item_id}/complete
  - PATCH /api/v1/treatment_plan/treatment-plans/{plan_id}/status
  - POST /api/v1/treatment_plan/treatment-plans
  - POST /api/v1/treatment_plan/treatment-plans/{plan_id}/close
  - POST /api/v1/treatment_plan/treatment-plans/{plan_id}/confirm
  - POST /api/v1/treatment_plan/treatment-plans/{plan_id}/contact-log
  - POST /api/v1/treatment_plan/treatment-plans/{plan_id}/generate-budget
  - POST /api/v1/treatment_plan/treatment-plans/{plan_id}/items
  - POST /api/v1/treatment_plan/treatment-plans/{plan_id}/link-budget
  - POST /api/v1/treatment_plan/treatment-plans/{plan_id}/reactivate
  - POST /api/v1/treatment_plan/treatment-plans/{plan_id}/reopen
  - POST /api/v1/treatment_plan/treatment-plans/{plan_id}/sync-budget
  - PUT /api/v1/treatment_plan/treatment-plans/{plan_id}
  - PUT /api/v1/treatment_plan/treatment-plans/{plan_id}/items/{item_id}
related_permissions:
  - treatment_plan.plans.read
  - treatment_plan.plans.write
  - treatment_plan.plans.confirm
  - treatment_plan.plans.close
  - treatment_plan.plans.reactivate
related_paths:
  - backend/app/modules/treatment_plan/frontend/pages/treatment-plans/index.vue
last_verified_commit: 0000000
---

# /treatment-plans

> _Scaffolded stub — replace with proper documentation when this module is next touched._

_Screen `/treatment-plans` of the `treatment_plan` module._

## Permissions

- `treatment_plan.plans.read`
- `treatment_plan.plans.write`
- `treatment_plan.plans.confirm`
- `treatment_plan.plans.close`
- `treatment_plan.plans.reactivate`

## What this screen does

_Documentation pending._

