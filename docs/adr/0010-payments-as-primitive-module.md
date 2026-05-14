# 0010 — Payments as a primitive module; billing depends on payments

- **Status:** accepted
- **Date:** 2026-05-13
- **Deciders:** Ramón Martínez (DentalPin Core)
- **Tags:** modules, finance, dental-operations

## Context

The original `billing` module owned the `Payment` model with a NOT-NULL
`invoice_id`. That coupling blocks three operational realities of a
dental clinic, validated with the user when scoping issue #53:

1. Patients commonly pay **before** an invoice exists — anticipos and
   partial cobros against an accepted budget.
2. Some clinics legitimately leave certain treatments off the invoice.
   The software cannot assume *executed ⇒ invoiced* nor expose KPIs
   that document the diff between paid/earned and invoiced — those
   metrics surface an operative clinics keep off-record, and visibility
   would be a stopper for adoption.
3. The clinic needs real-time financial visibility (patient credit,
   clinic receivable, refunds, breakdowns) that has nothing to do with
   invoice state.

A standalone `payments` module with patient-centric `Payment` and an
allocations layer (`budget | on_account`) cleanly supports anticipos.
A `Refund` entity replaces the legacy `is_voided` flag. The
`invoice ↔ payment` link is owned by billing in its own
`invoice_payments` table.

## Decision

`payments` is a primitive module. **`billing` depends on `payments`;
the reverse direction is forbidden.** Concretely:

- `payments.manifest.depends = ["patients", "budget"]`.
- `billing.manifest.depends = ["patients", "catalog", "budget", "payments"]`.
- `payments` never imports `app.modules.billing.*`.
- The link between an `Invoice` and a `Payment` lives in
  `billing.invoice_payments` — billing tracks the imputation in its own
  schema, payments stays invoice-agnostic.
- `Invoice.total_paid` and `Invoice.balance_due` are no longer stored
  columns; they are computed in `BillingService.compute_paid_summary`
  from `invoice_payments` minus proportional refunds.
- Reports of payment KPIs (collected, refunded, net, patient credit,
  receivable, aging, refunds, trends) live in `/api/v1/payments/reports/*`,
  inside the payments module.
- **No KPI must compare the `paid` axis with the `invoiced` axis**
  (e.g. "cobrado no facturado"). The fiscal axis stays in
  `/api/v1/reports/billing/*` (invoice-side aging, overdue) and is
  legitimate; the payment-side reports compare `paid ↔ earned ↔
  refunded` only.
- The `earned` signal for the patient ledger comes from event payloads
  (`odontogram.treatment.performed`, `treatment_plan.treatment_completed`)
  and is materialized in `patient_earned_entries`. Payments never
  imports odontogram or treatment_plan.

## Consequences

### Good

- Anticipos against budgets become first-class without faking an
  invoice. `Payment` is patient-centric.
- Off-books reality is supported without code paths labelled as such:
  treatments can be performed without an invoice, payments can be
  recorded without an invoice, and no metric surfaces the diff.
- Single source of truth for invoice paid amount (the
  `invoice_payments` rows + refunds), no cached column drift.
- `Refund` is the only payment-adjustment mechanism. Cleaner audit
  surface than the legacy `is_voided` flag.
- Module isolation holds: payments has zero imports from billing /
  odontogram / treatment_plan; billing imports payments freely
  (declared in `depends`).

### Bad / accepted trade-offs

- `Invoice.total_paid` and `Invoice.balance_due` now require an
  aggregation over `invoice_payments` + `refunds`. List endpoints pay
  for one extra query (batched). Acceptable at clinic-scale data sets.
- One asymmetric dependency direction means a future "billing without
  payments" deployment is not supported; payments is mandatory once
  billing is installed. Both are `removable=False` so this is
  intentional.
- The orchestrator `POST /api/v1/billing/invoices/{id}/payments`
  internally uses a payments-module `Payment` with an `on_account`
  allocation plus an `InvoicePayment` row. The invariant
  `Σ allocation.amount == payment.amount` is preserved without leaking
  invoice references into payments.

## Alternatives considered

- **Keep `Payment` inside billing with optional FK to invoice / budget.**
  Rejected — does not solve the off-books metric concern, keeps the
  `is_voided` flag, and conflates fiscal and operational axes in one
  schema.
- **Payments depending on billing.** Rejected — would mean the payment
  table needs to know about invoices to compute its allocations, which
  reintroduces the very coupling the extraction is meant to break.
- **Eventual consistency via events for Invoice status.** Rejected for
  money: refunds proportionally affect already-imputed payments and
  require a transactional recalc that fits the synchronous
  `recalc_invoice_status` path triggered by the `payment.refunded`
  handler.

## How to verify the rule still holds

- `backend/tests/test_module_isolation.py` confirms `payments` does not
  import `billing`, `odontogram`, or `treatment_plan`.
- `backend/app/core/plugins/manifest_validator.py` enforces that every
  cross-module FK resolves to a module listed in `manifest.depends`.
- Search guard: no `/api/v1/payments/reports/*` endpoint may return a
  field whose name suggests cross-axis comparison
  (`paid_vs_invoiced`, `unbilled_paid`, etc.). Reviewers flag in PR.
- `backend/scripts/generate_catalogs.py --check` keeps the event +
  module catalogs in sync; reviewers see new payment events at PR time.

## References

- Issue #53
- `backend/app/modules/payments/` (module root)
- `backend/app/modules/payments/CLAUDE.md`
- `backend/app/modules/billing/models.py` (InvoicePayment)
- `backend/app/modules/billing/migrations/versions/bil_0004_invoice_payments.py`
- ADR 0001 (modular plugin architecture)
- ADR 0003 (event bus over direct imports)
