# Budget module

Dental treatment quotes, versioning, signatures, PDF.

## Public API

Routes mounted at `/api/v1/budget/`.

## Dependencies

`manifest.depends = ["patients", "catalog"]`.

## Permissions

`budget.read`, `budget.write`, `budget.admin`.

## Events emitted

- `budget.sent`
- `budget.accepted`

## Events consumed

- `treatment_plan.treatment_added` / `treatment_plan.treatment_removed`
  / `treatment_plan.budget_sync_requested` — sync with treatment_plan.
- `odontogram.treatment.performed` — mark line items done when the
  underlying tooth treatment is performed.

## Lifecycle

- `removable=False`. Billing depends on accepted budgets.

## Gotchas

- **Budget ↔ treatment_plan is event-driven, never direct.** Don't
  import treatment_plan services from here, even though it's the
  obvious cross-module relation. See ADR 0003.
- **Budget versioning** keeps every prior version — never overwrite.
- **`budget.completed`** is published from the workflow when a budget
  becomes the basis for an invoice; the billing module subscribes.

## Related ADRs

- `docs/adr/0001-modular-plugin-architecture.md`
- `docs/adr/0003-event-bus-over-direct-imports.md`

## CHANGELOG

See `./CHANGELOG.md`.
