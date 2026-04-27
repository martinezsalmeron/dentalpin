# Changelog — billing module

## Unreleased

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
