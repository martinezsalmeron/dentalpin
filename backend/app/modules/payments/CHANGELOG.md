# payments — CHANGELOG

## Unreleased

- Initial module skeleton (issue #53).
- Models: `Payment`, `PaymentAllocation`, `Refund`, `PatientEarnedEntry`, `PaymentHistory`.
- Workflow: `record_payment`, `reallocate_payment`, `refund_payment`.
- Read services: `PaymentService`, `PaymentReadService`, `LedgerService`, `PaymentReportsService`.
- Endpoints under `/api/v1/payments/` covering CRUD, refunds, ledger, per-budget allocations, and reports (summary, by-method, by-professional, aging-receivables, refunds, trends).
- Events emitted: `payment.recorded`, `payment.allocated`, `payment.refunded`.
- Events consumed: `odontogram.treatment.performed`, `treatment_plan.treatment_completed` → upsert into `patient_earned_entries`.
- Migration `pay_0001_initial` on the `payments` branch (chains after `bud_0003`).
