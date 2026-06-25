# accounting_export — technical overview

Optional, removable, **model-free** module that exports billing data for
the clinic's accountant (*gestoría*). Issue #73.

## Responsibility

Produce a downloadable ZIP (`facturas.csv` + `cobros.csv`) for a chosen
period so an admin can hand bookkeeping data to the accountant without
copy-pasting from the UI. It **only reads** existing billing data; it
generates no fiscal documents (that is billing/verifactu territory).

## Architecture

- **No models, no tables.** The export is stateless, so uninstall never
  touches the schema. The module still carries an empty isolated Alembic
  branch (`accexp_0001`, no-op) to satisfy the removable-branch invariant
  (ADR 0002); the round-trip is trivial.
- **Data access via service API only.** Invoices (and their allocated
  payments) are fetched through `InvoiceService.list_for_export` in the
  `billing` module. This module imports no billing/payments models and
  declares `depends = ["billing", "payments"]`.
- **Formats via stdlib.** CSV with stdlib `csv` (configurable `,`/`;`
  separator; `;` emits comma decimals + UTF-8 BOM for Excel-ES), bundled
  with stdlib `zipfile`. No third-party dependencies.

## Off-books boundary (critical)

The export is **invoice-centric**: only issued invoices and the payments
**allocated to them** (`InvoicePayment`) are exported. The raw `Payment`
ledger and the paid-vs-invoiced diff are never surfaced — see
[ADR 0010](../../adr/0010-payments-as-primitive-module.md). A cash payment
not tied to any invoice does not appear. Drafts are excluded.

## Endpoints

Mounted at `/api/v1/accounting_export/`.

| Method | Path       | Permission                      | Returns |
|--------|------------|---------------------------------|---------|
| GET    | `/preview` | `accounting_export.export.read` | Counts, totals, 10-row sample |
| GET    | `/run`     | `accounting_export.export.run`  | ZIP (`facturas.csv` + `cobros.csv`) |

Date presets (current/previous month/quarter, year-to-date) are computed
client-side; the backend only takes concrete `date_from`/`date_to`.

## Events

Emits none. Consumes none.

## Out of scope (follow-ups)

XLSX, ContaPlus/A3CON diary entries, per-invoice FacturaE, push-to-cloud
integrations, export history. Verifactu/AEAT data is excluded (verifactu
is optional and can't be a hard dependency); if ever wanted, read it from
the billing-owned `Invoice.compliance_data['ES']` without adding a dep.
