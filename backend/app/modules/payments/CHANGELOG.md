# payments — CHANGELOG

## Unreleased

### Added (lists redesign, 2026-05-14)

- `POST /api/v1/payments/summary/by-budgets` — bulk per-budget
  collected/pending/payment_status (cap 100 ids). Off-books safe.
- `POST /api/v1/payments/summary/by-patients` — bulk per-patient
  total_paid/debt/on_account (cap 100 ids). Off-books safe.
- `GET  /api/v1/payments/filters/budgets-by-status` — clinic-wide
  budget id set by payment status (cap 1000 ids, `truncated` flag).
- `GET  /api/v1/payments/filters/patients-with-debt` — clinic-wide
  patient id set with debt ≥ min_debt (cap 1000 ids).
- New slot fillers registered: `patients.list.row.financial`,
  `patients.list.filter`, `budget.list.row.payments`,
  `budget.list.filter`. Enables /patients debt column + "Con deuda"
  filter and /budgets payment-progress column + "Cobro" filter
  without violating module isolation.
- `GET /api/v1/payments` accepts new params: `has_refunds`,
  `has_unallocated`, `amount_min`, `amount_max`, `sort=field:dir`
  (whitelist: `payment_date`, `amount`, `created_at`).
- `/payments` UI rewritten on top of `DataListLayout` + `FilterBar`
  + `useListQuery`. Chips for method, date range with presets,
  paciente como autocomplete (sustituye al campo UUID).
- Initial module skeleton (issue #53).
- Models: `Payment`, `PaymentAllocation`, `Refund`, `PatientEarnedEntry`, `PaymentHistory`.
- Workflow: `record_payment`, `reallocate_payment`, `refund_payment`.
- Read services: `PaymentService`, `PaymentReadService`, `LedgerService`, `PaymentReportsService`.
- Endpoints under `/api/v1/payments/` covering CRUD, refunds, ledger, per-budget allocations, and reports (summary, by-method, by-professional, aging-receivables, refunds, trends).
- Events emitted: `payment.recorded`, `payment.allocated`, `payment.refunded`.
- Events consumed: `odontogram.treatment.performed`, `treatment_plan.treatment_completed` → upsert into `patient_earned_entries`.
- Migration `pay_0001_initial` on the `payments` branch (chains after `bud_0003`).
- `BudgetPaymentsCard` redesign compacto: resumen `Cobrado / Total` con barra de progreso, estado de pendiente en una línea, historial con icono de método + fecha relativa, único CTA "Cobrar" en el header (oculto cuando saldado). Mueve la tarjeta al top del sidebar del detalle de presupuesto (antes caía al fondo del grid).
- `AllocationResponse` ahora expone `method` (del pago padre) — aditivo, sin queries nuevas (ya estaba joinedloaded).
- `BudgetCollectModal` usa `useCurrency().format` en lugar de un `Intl.NumberFormat` inline; prop `currency` retirado (era vestigial).
- `PatientPaymentsPanel` registrado en el slot `patient.detail.administracion.payments` (host: módulo `patients`). Surfacing del ledger del paciente (banner deuda/crédito, KPIs `total_paid` / `clinic_receivable` / `on_account_balance`, sidebar con saldo a favor y último pago, timeline cronológico con menú overflow por pago para reembolsar) dentro del tab Administración de la ficha. Consume `GET /payments/patients/{id}/ledger` ya existente; sin endpoints nuevos.
- `RefundConfirmModal` — formulario corto (importe, método, motivo, nota) usado desde el menú overflow del timeline para `POST /payments/{id}/refunds`.
