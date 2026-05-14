# Changelog — billing module

## Unreleased

### Added (lists redesign, 2026-05-14)

- `GET /api/v1/billing/invoices` accepts `sort=field:dir` (whitelist:
  `issue_date`, `due_date`, `total`, `created_at`, `invoice_number`).
- `/invoices` list page rewritten on `DataListLayout` + `FilterBar` +
  `useListQuery`. Card view <md, URL-synced filters, sort dropdown,
  date range filter in the main toolbar. Existing compliance slots
  (`invoice.list.toolbar.filters`, `invoice.list.row.meta`)
  preserved.

- **Payment domain extracted to its own `payments` module (issue #53, ADR 0010).**
  - Billing no longer owns the `Payment` model, `PaymentService`, or
    `InvoiceWorkflowService.record_payment` / `void_payment`. Those move
    to `app.modules.payments`.
  - New `InvoicePayment` model + `bil_0004_invoice_payments` migration —
    one row per imputation of a Payment to an Invoice. Multiple rows
    per invoice (parcial cobros) and per payment (allocations across
    invoices) are supported.
  - `Invoice.total_paid` / `Invoice.balance_due` columns dropped. The
    values are computed by `BillingService.compute_paid_summary` from
    `invoice_payments` minus proportional refunds.
  - New endpoint `POST /api/v1/billing/invoices/{id}/payments` is the
    "factura + cobro" orchestrator: it creates a Payment via the
    payments module, links it via `InvoicePayment`, and recomputes the
    invoice status. For anticipos against budgets, use the payments
    module directly.
  - New event subscription `payment.refunded` recomputes the invoice
    status of any invoice with an `InvoicePayment` pointing to the
    refunded payment.
  - `BillingComplianceHook.on_payment_recorded` was previously defined
    but never invoked. The new orchestrator now calls it after creating
    the link (placeholder until verifactu wires it up).
  - Manifest: `depends` now lists `"payments"`.

- `PatientBillingSummary` (patient detail → Administración → Facturación)
  now paginates invoices at page_size=20 with the shared `PaginationBar`,
  replacing the previous hard-coded `page_size: 100` single-page dump.
- **Generic compliance summary in invoice list** — `InvoiceListResponse`
  now exposes `compliance_data` (the same JSONB the model already
  carries). Compliance modules (Verifactu et al.) read it via slots
  to render their own badge in each row without billing knowing the
  shape per country.
- **Generic `compliance_severity` query filter** on
  `GET /api/v1/billing/invoices`. Whitelisted values
  (`ok|warning|pending|error`). Filter is country-agnostic — applies
  via JSONB path over any country key whose `severity` matches. The
  vocabulary is shared across compliance modules; billing never
  imports them.
- **Three new module slots** in the invoice screens for compliance
  modules to plug into:
  - `invoice.list.row.meta` — extra chip next to the status badge in
    each list row. Ctx: `{invoice, clinic}`.
  - `invoice.list.toolbar.filters` — extra filter widgets in the list
    toolbar. Ctx: `{severity, onChange, clinic}`.
  - `invoice.detail.header.meta` — extra badge next to the invoice
    number/status in the detail header. Ctx: `{invoice, clinic}`.
- **`PATCH /api/v1/billing/invoices/{id}/billing-party`** — edit
  `billing_name` / `billing_tax_id` / `billing_address` on an issued
  invoice when the country compliance hook signals the latest fiscal
  record is correctable (e.g. Verifactu `rejected`). Triggers the
  hook's `regenerate_after_party_change` so the user does not have to
  chase the compliance queue. Optimistic locking via
  `expected_updated_at`.
- **`Invoice.pdf_stale`** boolean (migration `bil_0002`). Compliance
  hooks set it to `True` after regenerating their fiscal record so
  the previously-rendered PDF (with stale QR / huella) is flagged in
  the UI for re-download.
- **`BillingComplianceHook` interface extended** with
  `can_edit_billing_party()` (gates the new PATCH endpoint) and
  `regenerate_after_party_change()` (re-renders the compliance
  record after a party edit). Default impls are no-ops so existing
  hooks keep working.
- Added per-module `CLAUDE.md` for AI-agent context (2026-04-27).
- `InvoicePDFService.generate_pdf()` accepts an optional
  `extra_pdf_data` dict produced by a registered
  `BillingComplianceHook.enhance_pdf_data()`. The PDF endpoints
  (`GET /invoices/{id}/pdf` and its preview sibling) now resolve the
  hook from `BillingHookRegistry` and forward its dict so country
  modules can inject a QR (`compliance_qr_png_b64`) and legal
  notices. Billing remains country-agnostic — it only reads the
  generic dict it receives.
- Invoice detail page exposes a generic `<ModuleSlot
  name="invoice.detail.compliance">` so country compliance modules
  (Verifactu-ES today, factur-x-FR or sdi-IT later) can render a
  status panel next to the totals without billing importing them.

## 0.1.0 — initial

- Invoice + credit note workflow with PDF generation.
- Payment recording (full and partial).
- `BillingComplianceHook` extension point for compliance modules.
- Events: `invoice.issued`, `invoice.sent`, `invoice.paid`.
