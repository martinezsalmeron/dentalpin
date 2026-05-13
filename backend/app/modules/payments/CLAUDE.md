# Payments module

Patient-centric collections, allocations to budgets / on-account,
refunds, patient ledger, and dental payment reports.

Issue #53. ADR 0010 documents the architectural inversion: billing
depends on payments, the reverse is forbidden. The link
``invoice ↔ payment`` lives in the billing module's own
``invoice_payments`` table; payments does not import billing.

## Public API

Routes mounted at `/api/v1/payments/`.

| Path | Method | Permission |
|---|---|---|
| `/` | GET | `payments.record.read` |
| `/` | POST | `payments.record.write` |
| `/{id}` | GET | `payments.record.read` |
| `/{id}/reallocate` | POST | `payments.record.write` |
| `/{id}/refunds` | GET | `payments.record.read` |
| `/{id}/refunds` | POST | `payments.record.refund` |
| `/patients/{patient_id}/ledger` | GET | `payments.record.read` |
| `/budgets/{budget_id}/allocations` | GET | `payments.record.read` |
| `/reports/summary` | GET | `payments.reports.read` |
| `/reports/trends` | GET | `payments.reports.read` |
| `/reports/by-method` | GET | `payments.reports.read` |
| `/reports/by-professional` | GET | `payments.reports.read` |
| `/reports/aging-receivables` | GET | `payments.reports.read` |
| `/reports/refunds` | GET | `payments.reports.read` |

## Dependencies

`manifest.depends = ["patients", "budget"]`. **Never add billing** —
that would create a cycle (billing.depends includes payments). Read
ADR 0010 before touching the dependency list.

## Permissions

`payments.record.{read,write,refund}`, `payments.reports.read`.

Refund is admin/dentist by default. Clinic admins may grant
`payments.record.refund` to receptionists via the roles UI — no code
change required.

## Events emitted

- `payment.recorded` — payload `{clinic_id, payment_id, patient_id, amount, currency, method, payment_date, occurred_at}`.
- `payment.allocated` — payload `{clinic_id, payment_id, allocation_id, target_type, target_id, amount, previous_target_type, previous_target_id, occurred_at}`. Fired on create and on reallocate.
- `payment.refunded` — payload `{clinic_id, payment_id, refund_id, amount, reason_code, occurred_at}`.

## Events consumed

| Event | Handler | Effect |
|---|---|---|
| `odontogram.treatment.performed` | `on_treatment_performed` | Upsert `PatientEarnedEntry` |
| `treatment_plan.treatment_completed` | `on_plan_item_completed` | Upsert `PatientEarnedEntry` (idempotent vs odontogram) |

Both handlers require `unit_price`/`price_snapshot` in the payload. If
the publisher omits it, the entry is skipped with a warning — see
gotchas below.

## Frontend slots consumed

| Slot | Component | Permission |
|---|---|---|
| `budget.detail.sidebar` | `BudgetPaymentsCard` (cobrado / pendiente / allocations + "Cobrar" CTA) | `payments.record.read` |
| `reports.categories` | `PaymentsReportEntry` (card on `/reports` linking to `/reports/payments`) | `payments.reports.read` |

Registered in `frontend/plugins/slots.client.ts`. The card receives
`ctx = { budget }` from the host page and never imports anything from
`budget`'s code — only the public allocations endpoint.

## Lifecycle

- `installable=True`, `auto_install=True`, `removable=False`.
- Fiscal/contable retention forbids data deletion; uninstall is
  blocked by manifest.

## Gotchas

- **No `is_voided` flag.** Total reverso is `Refund(amount=Payment.amount)`.
  Don't reintroduce the legacy flag — the report stack relies on
  Refund rows being the only adjustment vector.
- **No paid-vs-invoiced metrics.** Reports must not subtract `paid` from
  `invoiced` or `earned` from `invoiced`. Dental clinics legitimately
  leave some treatments off the invoice; exposing that diff documents
  the operative and is a stopper for adoption. See ADR 0010.
- **No imports from odontogram or treatment_plan.** Earned data enters
  through event payloads only. Add fields to the publisher when needed —
  the snapshot pattern is the contract.
- **Allocations sum invariant** is enforced in the service, not the DB.
  Schemas validate at the boundary so 4xx never reach the workflow.
- **Cross-clinic budgets** are rejected by the workflow. UI must filter
  budget pickers to current clinic.
- **`Clinic.currency` snapshot.** Payments capture the clinic currency
  at write time. If a clinic ever switches currency, historical
  payments stay in the old one (correct behaviour).

## Related ADRs

- `docs/adr/0001-modular-plugin-architecture.md`
- `docs/adr/0003-event-bus-over-direct-imports.md`
- `docs/adr/0010-payments-as-primitive-module.md`

## CHANGELOG

See `./CHANGELOG.md`.
