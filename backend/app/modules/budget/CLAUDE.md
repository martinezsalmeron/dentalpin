# Budget module

Dental treatment quotes, versioning, signatures, PDF.

## Public API

Routes mounted at `/api/v1/budget/`. Authenticated subset:

- CRUD + version + signature workflow (legacy).
- `POST /budgets/{id}/{renegotiate,accept-in-clinic,resend,
  send-reminder,set-public-code,unlock-public}` (workflow rework).

Public subset (no staff auth, 2-factor verification — ADR 0006) under
`/api/v1/public/budgets/{token}/`:

- `GET    /meta`
- `POST   /verify`           (rate-limited; sets HttpOnly cookie)
- `GET    /`                 (cookie-protected; idempotent viewed_at)
- `POST   /accept`           (cookie-protected)
- `POST   /reject`           (cookie-protected)

## Dependencies

`manifest.depends = ["patients", "catalog", "odontogram"]`.

## Permissions

`budget.read`, `budget.write`, `budget.admin`,
`budget.renegotiate`, `budget.accept_in_clinic`.

## Events emitted

- `budget.sent`
- `budget.accepted` (snapshot payload includes `accepted_via`,
  `plan_id`).
- `budget.rejected` (snapshot payload with `rejection_reason`,
  `plan_id`).
- `budget.expired` (snapshot payload with `days_overdue`, `plan_id`).
- `budget.renegotiated` (snapshot payload with `plan_id`).
- `budget.viewed` (idempotent first-open, snapshot payload).
- `budget.reminder_sent` (snapshot payload with `milestone_days`).

## Events consumed

- `treatment_plan.treatment_added` / `treatment_plan.treatment_removed`
  / `treatment_plan.budget_sync_requested` — sync with treatment_plan
  via **snapshot payloads only** (no cross-module ORM imports).
- `odontogram.treatment.performed` — mark line items done when the
  underlying tooth treatment is performed.

## Lifecycle

- `removable=False`. Billing depends on accepted budgets.

## Gotchas

- **Budget → treatment_plan is event-driven, never direct.** Don't
  import treatment_plan services or models from here. The reverse
  direction (treatment_plan → budget) is allowed because budget is in
  treatment_plan's depends. See ADR 0003.
- **Snapshot-only event handlers.** `_on_treatment_added_to_plan` and
  friends consume the data carried in the payload (catalog_item_id,
  tooth, surfaces, unit_price, budget_id) — no fetches against the
  publisher's tables.
- **Plan reverse-lookup uses raw SQL** (`_lookup_plan_id`) instead of
  importing the `TreatmentPlan` model, so event payloads can carry
  `plan_id` without violating ADR 0003.
- **Budget versioning** keeps every prior version — never overwrite.
- **Public-link sessions are per-token** (cookie path scoped to
  `/api/v1/public/budgets/{token}`) so a stolen cookie from one
  budget cannot unlock another.
- **`BUDGET_PUBLIC_SECRET_KEY`** signs the public session cookies and
  is independent from the global `SECRET_KEY`. Falls back in dev only.
- ``budget.completed`` no longer exists. The transition
  ``accepted → completed`` and the manual "Mark completed" button
  were removed in 2026-04: ``completed`` was a bookkeeping flag
  with no auto-trigger and no real consumer. Use invoice paid /
  fully invoiced as the financial-closure signal instead.

## Related ADRs

- `docs/adr/0001-modular-plugin-architecture.md`
- `docs/adr/0003-event-bus-over-direct-imports.md`
- `docs/adr/0006-budget-public-link-2-factor-auth.md`

## CHANGELOG

See `./CHANGELOG.md`.
