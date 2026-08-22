# India GST — Installation & Operation Manual

> **Optional module — India only.** CGST/SGST/IGST billing compliance for
> Indian dental clinics under the GST regime (CGST Act 2017). Handles
> GSTIN capture, place-of-supply-driven tax split, SAC code defaults,
> FY-scoped document numbering, credit-note reversal, and a GST
> reconciliation report with CSV export. E-invoice integration is
> scaffolding only in v1 (no live GSP/IRP provider wired in).

---

## Contents

1. [What this module does](#1-what-this-module-does)
2. [Architecture & module boundaries](#2-architecture--module-boundaries)
3. [Installation](#3-installation)
4. [Setup walkthrough](#4-setup-walkthrough)
5. [Daily operation](#5-daily-operation)
6. [Tax calculation engine](#6-tax-calculation-engine)
7. [PDF invoice integration](#7-pdf-invoice-integration)
8. [E-invoice scaffolding](#8-e-invoice-scaffolding)
9. [Data model](#9-data-model)
10. [API endpoints](#10-api-endpoints)
11. [Permissions](#11-permissions)
12. [Frontend components](#12-frontend-components)
13. [Testing](#13-testing)
14. [Troubleshooting](#14-troubleshooting)
15. [Known limitations & roadmap](#15-known-limitations--roadmap)

---

## 1. What this module does

When a clinic in India (`clinic.settings.country == "IN"`) has the module
enabled and issues an invoice, India GST silently:

1. **Splits each line's already-computed `line_tax`** into CGST + SGST
   (intra-state) or IGST (inter-state) — never recomputes tax.
2. **Snapshots the full GST context** (supplier GSTIN, recipient GSTIN,
   place of supply, tax type, CGST/SGST/IGST totals, GST document number)
   into `invoice.compliance_data['IN']` at issue time. This snapshot is
   immutable — later edits to settings never change how an issued invoice
   renders or audits.
3. **Assigns a FY-scoped GST document number** (`FAC/FY26-27/0001`)
   following India's April–March financial year.
4. **Persists line-level GST breakdown** in `india_gst_invoice_items`
   for reconciliation reporting.
5. **Enhances the PDF invoice** with a GST breakdown section and
   overrides "VAT"/"Tax" labels to "GST" for Indian clinics.
6. **Shows a compliance badge** on the invoice list and detail page
   indicating GST status (success / warning / needs attention).

For credit notes, the hook inherits the place of supply from the
original invoice and splits the already-negative `line_tax` without
re-negation.

---

## 2. Architecture & module boundaries

DentalPin is international software; GST is India-only. The india_gst
module is therefore optional, country-specific, and isolated — mirroring
the `verifactu` (Spain/AEAT) module's architecture.

**Module dependencies (declared in `manifest.depends`):**
- `billing` — to register the `BillingComplianceHook` for country `IN`.
- `catalog` — to read `TreatmentCatalogItem` for SAC-default resolution.

**What india_gst does NOT do:**
- Modify `invoices`/`invoice_items` tables (billing stays
  fiscal-neutral). All GST data lives in `india_gst_*` tables and
  `invoice.compliance_data['IN']` (JSONB).
- Add columns to core/billing/catalog tables.
- Lock billing flow. If india_gst is disabled, billing operates as if
  the module wasn't installed.

**How it plugs in:**
- Hook is registered via `BillingHookRegistry.register(IndiaGstHook())`
  on every backend boot (in `IndiaGstModule.__init__`). Routing is
  per-invoice based on `clinic.settings.country == "IN"`.
- The hook reads from its own tables (`india_gst_settings`,
  `india_gst_catalog_items`, `india_gst_invoice_items`,
  `india_gst_einvoice_submissions`) plus reads from `clinics`,
  `invoices`, and `invoice_items`.

**Cross-module imports:** none outside `manifest.depends`
(`billing`, `catalog`). The module has no `KNOWN_VIOLATIONS` entries.

---

## 3. Installation

### 3.1 Build the backend image

```bash
docker compose up -d --build backend
```

### 3.2 Run migrations

```bash
docker compose exec backend alembic upgrade heads
```

This applies the migration on the `india_gst` Alembic branch:
- `igst_0001_initial` — settings, catalog items, invoice items,
  FY document sequences, e-invoice submissions.

### 3.3 Install from the admin UI

1. Sign in as admin.
2. Go to `Admin → Modules`.
3. Find **india_gst** in the list and click **Install**.
4. The installer:
   - Confirms migrations are at head.
   - Registers `IndiaGstHook` for country `IN`.
   - Promotes the record to `state=installed`.
   Install never touches clinic data — configuration happens in the
   settings page (the auto-configure action creates SAC defaults and
   the `GST 18%` VAT type idempotently).
5. The india_gst settings page appears at `/settings/india-gst`.

In dev, Nuxt watches `frontend/modules.json` and restarts itself when
the backend rewrites it on install/uninstall — no manual step required.

### 3.4 Uninstall

Uninstall is guarded: if **any** `IndiaGstInvoiceItem` is linked to a
non-draft invoice (issued/partial/paid/credit-note), the uninstall
raises `RuntimeError` and aborts. This prevents orphaning the
CGST/SGST/IGST breakdown that was already communicated to the customer.

To uninstall, void or credit-note all issued invoices with GST data
first, then retry from `Admin → Modules`.

---

## 4. Setup walkthrough

Once installed, every clinic that wants to issue GST-compliant invoices
must complete these steps:

### Step 1 — Set clinic country to India

1. Go to `Configuration` → `Clinic information` → `Edit`.
2. Set **Country** to *India* (`IN`).
3. Save. The india_gst hook only activates for clinics with
   `country == "IN"`.

### Step 2 — Configure GST profile

1. Go to `/settings/india-gst`.
2. Fill in:
   - **Trade name** — legal trading name (shown on invoices).
   - **GSTIN** — the clinic's own 15-digit GSTIN (e.g.
     `33ABCDE1234F1Z5`). Validated against the CBIC format regex.
   - **Registration type** — `regular`, `composition`, `unregistered`,
     or `exempt`. Only `regular` drives invoicing logic in v1.
   - **Clinic state** — the 2-digit state code (e.g. `33` for Tamil
     Nadu). Used to determine intra vs inter-state tax.
   - **Turnover threshold** — for e-invoice applicability
     (scaffolding only in v1).
   - **Show GSTIN on invoice** / **Show SAC on invoice** — display
     preferences for the PDF.
3. Click **Save**.

### Step 3 — Configure SAC code defaults

Every treatment catalog item should have a SAC (Services Accounting
Code) for GST compliance. The default dental SAC is `999312` (Human
health and social care services).

1. Go to `/settings/india-gst` → **SAC defaults** section.
2. Review the **Missing SAC** table — lists treatments without a SAC
   code, rendered in the viewer's UI locale.
3. Click **Auto-configure** to stamp `999312` on every missing item in
   one click. This is additive only — existing SAC codes are never
   overwritten.
4. Optionally, edit individual SAC codes per treatment.

### Step 4 — Set recipient GSTIN on invoices

The recipient's (patient's) GSTIN is stored in `Invoice.billing_tax_id`
(billing-owned, generic column) — not in india_gst tables. Enter it
in the invoice's billing info section before issuing.

---

## 5. Daily operation

### Issuing an invoice

The flow is automatic — billing-side UX is unchanged. From the user's
perspective:

1. Create an invoice (draft). Add items. Set place of supply and SAC
   codes in the GST panel if needed.
2. Click **Emitir factura / Issue invoice**. Workflow validates billing
   data, runs the `validate_before_issue` hook:
   - India GST checks: place of supply is set (required for tax
     determination), registration type is `regular`.
3. The hook splits each line's `line_tax` into CGST+SGST or IGST,
   assigns the GST document number, and writes the compliance snapshot
   into `invoice.compliance_data['IN']`.
4. The invoice transitions to `issued`. The GST panel on the invoice
   detail page shows the full breakdown (CGST/SGST/IGST totals, GST
   document number, place of supply, supplier/recipient GSTINs,
   e-invoice status).

### Credit notes

Credit notes inherit the place of supply from the original invoice
(not their own `compliance_data`, which is empty until issued). The
hook splits the already-negative `line_tax` without re-negation —
`cgst_amount + sgst_amount` (or `igst_amount`) always reconciles
exactly to `line_tax`.

### GST reconciliation report

Available at `/reports/india-gst`:

- **Summary** — CGST/SGST/IGST totals, invoice count, credit note
  count, breakdown by place of supply.
- **Transactions** — line-by-line listing of all reportable invoices
  (issued/partial/paid) and credit notes with GST document number,
  recipient GSTIN, place of supply, taxable value, and tax split.
- **CSV export** — downloadable reconciliation file for accounting.

Drafts and cancelled invoices are excluded from all reports.

---

## 6. Tax calculation engine

### Core principle: split, never recompute

`compute_gst_breakdown` in `service.py` takes each line's
already-computed `line_tax` (from billing's standard VAT calculation)
and splits it:

- **Intra-state** (`clinic_state == place_of_supply`):
  - CGST = SGST = `line_tax / 2`, each rounded HALF_UP per head —
    the two heads are levied at the same rate on the same value and
    must be equal (GSTR-1 reconciliation rejects asymmetric heads).
    On odd-paise lines the pair may differ from `line_tax` by ±0.01
    (expected head-wise rounding).
  - CGST rate = SGST rate = `vat_rate / 2`
- **Inter-state** (`clinic_state != place_of_supply`):
  - IGST = `line_tax` (full amount)
  - IGST rate = `vat_rate`

This is **sign-agnostic** — works unmodified for negative (credit-note)
amounts, since it only ever adds/subtracts the line's own `line_tax`.

### Place of supply

Stored as a 2-digit state code (from `constants.INDIA_STATES`), never
as a free-text display string. Codes are compared directly.

If either `clinic_state` or `place_of_supply` is missing, the hook
blocks invoice issuance with a validation error.

### Financial year document numbering

GST document numbers are `{prefix}/FY{yy}-{yy+1}/{seq}`, where India's
financial year runs April through March:

- An invoice dated March 2026 → `FY25-26`
- An invoice dated April 2026 → `FY26-27`

The serial comes from the module's own `india_gst_document_sequences`
counter — one row per `(clinic, prefix, FY)`, incremented under
`SELECT … FOR UPDATE`, unique-constrained, restarting at 1 each April.
It deliberately does **not** reuse billing's `sequential_number`, which
resets on the calendar year and would repeat numbers within one FY
between January and March (GST Rule 46(b) requires the serial to be
unique within the FY). Idempotent re-issue keeps the number already in
the snapshot.

### Registration types

Only `registration_type == "regular"` computes GST in v1.
Composition/Unregistered/Exempt are stored but the hook returns `{}`
(no GST rows) — composition-scheme rules are materially different and
out of scope for v1.

---

## 7. PDF invoice integration

The `IndiaGstHook.enhance_pdf_data` method enriches the PDF generation
with:

- **Label overrides** — "VAT" and "Tax" labels are replaced with "GST"
  for Indian clinics.
- **GST breakdown section** — a structured HTML panel showing:
  - GST document number
  - Place of supply
  - Supplier GSTIN / Recipient GSTIN
  - Tax type (Intra-state / Inter-state)
  - CGST / SGST / IGST totals
- **E-invoice status** badge (when applicable)

The hook hands billing a structured `compliance_section` dict
(`title`, `rows` of `{label, value, amount?}`, optional `hint`);
`billing/pdf.py` renders **and escapes** it after the payment-info
block and before legal notices — hooks never pass HTML across the
module boundary.

### Tamil language support

PDF generation supports `locale=ta` (Tamil). Tamil labels are defined
in `pdf.py::_get_labels` and the CSS font-family includes
`'Noto Sans Tamil'` (installed via `fonts-noto-core` in the Dockerfile).

---

## 8. E-invoice scaffolding

E-invoice in v1 only tracks **applicability** per invoice:

- `IndiaGstEinvoiceSubmission` holds one row per invoice with
  `state` (`not_required` below the turnover threshold,
  `not_configured` above it) and `provider_error_message`.
- The retry endpoint always returns `409` — never a fabricated success.
- There is no provider adapter, submission queue, or IRN storage —
  those arrive together with a real GSP/IRP integration, which will
  add its own columns and provider config then.

---

## 9. Data model

### `india_gst_settings` — one row per clinic

| Column | Type | Purpose |
|--------|------|---------|
| `clinic_id` | UUID, unique | Owner |
| `trade_name` | str(200) | Legal trading name for invoices |
| `gstin` | str(15) | Clinic's own (supplier) GSTIN |
| `registration_type` | str(20) | `regular` / `composition` / `unregistered` / `exempt` |
| `clinic_state` | str(2) | 2-digit state code (CBIC) |
| `turnover_threshold` | Numeric(14,2) | E-invoice applicability threshold |
| `show_gstin_on_invoice` | bool | Display preference |
| `show_sac_on_invoice` | bool | Display preference |

### `india_gst_catalog_items` — SAC defaults per treatment

| Column | Type | Purpose |
|--------|------|---------|
| `clinic_id` | UUID | Owner |
| `catalog_item_id` | UUID, unique | FK to `treatment_catalog_items` |
| `sac_code` | str(10) | Services Accounting Code |
| `notes` | Text | Free text notes |

### `india_gst_invoice_items` — CGST/SGST/IGST split per invoice line

| Column | Type | Purpose |
|--------|------|---------|
| `clinic_id` | UUID | Owner |
| `invoice_item_id` | UUID, unique | FK to `invoice_items` |
| `sac_code` | str(10) | SAC code at issue time |
| `tax_type` | str(10) | `intra` or `inter` |
| `cgst_rate` / `cgst_amount` | Numeric | CGST split |
| `sgst_rate` / `sgst_amount` | Numeric | SGST split |
| `igst_rate` / `igst_amount` | Numeric | IGST split |

### `india_gst_document_sequences` — FY serial counter

| Column | Type | Purpose |
|--------|------|---------|
| `clinic_id` | UUID | Owner |
| `prefix` | str(20) | Series prefix (e.g. `GST`, `CN`) |
| `fy_label` | str(8) | e.g. `FY26-27`; unique with clinic+prefix |
| `last_number` | int | Last allocated serial |

### `india_gst_einvoice_submissions` — e-invoice state per invoice

| Column | Type | Purpose |
|--------|------|---------|
| `clinic_id` | UUID | Owner |
| `invoice_id` | UUID, unique | FK to `invoices` |
| `state` | str(20) | `not_required` / `not_configured` (v1 never advances further) |
| `provider_error_message` | Text | Error details |

---

## 10. API endpoints

Base prefix: `/api/v1/india_gst/`. Every endpoint requires `ClinicContext`
(auth + clinic membership).

| Method | Path | Permission | Notes |
|--------|------|------------|-------|
| GET | `/settings` | `india_gst.settings.read` | Read or lazily create settings row |
| PUT | `/settings` | `india_gst.settings.configure` | Update GST profile (GSTIN, state, registration type, etc.) |
| GET | `/catalog-defaults` | `india_gst.catalog.manage` | List configured + missing SAC defaults |
| POST | `/catalog-defaults/autoconfigure` | `india_gst.catalog.manage` | Stamp default SAC (`999312`) on all missing items |
| PUT | `/catalog-defaults/{catalog_item_id}` | `india_gst.catalog.manage` | Set SAC code for a specific treatment |
| POST | `/tax-preview` | `india_gst.settings.read` | Stateless GST breakdown preview for draft invoices |
| PUT | `/invoices/{invoice_id}` | `billing.write` | Update draft-only GST fields (place of supply, SAC codes) |
| GET | `/invoices/{invoice_id}/einvoice` | `india_gst.settings.read` | E-invoice status |
| POST | `/invoices/{invoice_id}/einvoice/retry` | `india_gst.settings.configure` | Always 409 in v1 (no provider) |
| GET | `/reports/summary` | `india_gst.reports.read` | GST reconciliation summary |
| GET | `/reports/transactions` | `india_gst.reports.read` | Line-by-line transaction listing |
| GET | `/reports/export` | `india_gst.reports.read` | CSV export |

---

## 11. Permissions

Module returns these from `get_permissions()` (registry namespaces to
`india_gst.*`):

```
settings.read
settings.configure
catalog.manage
reports.read
```

Default role grants:
- `admin` → `*` (all)
- `dentist` → `reports.read`, `settings.read`
- `hygienist`, `assistant` → `settings.read`
- `receptionist` → `reports.read`, `settings.read`

`settings.read` goes to every clinical role because the invoice
form/detail panels call tax-preview and e-invoice status mid-invoicing.

Editing GST fields on a *draft* invoice reuses billing's own
`billing.write` permission: the operation IS invoice editing, so
whoever billing lets edit invoices can set place of supply / SAC —
gating it behind an india_gst permission would drift out of sync with
billing's role grants (cross-module gating precedent: agenda →
clinical_notes).

---

## 12. Frontend components

### Composables

| Composable | File | Purpose |
|------------|------|---------|
| `useIndiaGst` | `composables/useIndiaGst.ts` | API client for all india_gst endpoints (settings, catalog defaults, tax preview, invoice GST fields, e-invoice status) |
| `useIndiaGstStates` | `composables/useIndiaGstStates.ts` | India state/UT code→name mapping and select options |

### Components

| Component | File | Purpose |
|-----------|------|---------|
| `IndiaGstBadge` | `components/india-gst/IndiaGstBadge.vue` | Compact GST status badge for invoice list/detail. Shows "Needs attention" warning when an Indian clinic's non-draft invoice is missing GST data |
| `IndiaGstInvoicePanel` | `components/india-gst/IndiaGstInvoicePanel.vue` | Read-only GST breakdown panel on invoice detail (document number, place of supply, GSTINs, CGST/SGST/IGST totals, e-invoice status) |
| `IndiaGstInvoiceFormPanel` | `components/india-gst/IndiaGstInvoiceFormPanel.vue` | Editable GST fields on draft invoices (place of supply, SAC codes per line) |
| `IndiaGstListFilter` | `components/india-gst/IndiaGstListFilter.vue` | Filter component for the invoice list |
| `IndiaGstUnregisteredBanner` | `components/india-gst/IndiaGstUnregisteredBanner.vue` | Global banner shown when india_gst is installed but no GSTIN is configured |
| `SettingsCardsSlot` | `components/india-gst/SettingsCardsSlot.vue` | Slot component for settings page cards |

### Pages

| Page | File | Purpose |
|------|------|---------|
| GST Report | `pages/reports/india-gst.vue` | Reconciliation report with summary and transaction table |
| GST Settings | `pages/settings/india-gst/index.vue` | GST profile configuration and SAC defaults management |

### i18n

Translations are provided in three locales:
- `i18n/locales/en.json` — English
- `i18n/locales/es.json` — Spanish
- `i18n/locales/ta.json` — Tamil

### Utility functions

| Utility | File | Purpose |
|---------|------|---------|
| `gstBadgeLogic` | `utils/gstBadgeLogic.ts` | Pure logic extracted from badge/panel components for unit testing (badge color/label computation, e-invoice color/label, Indian clinic detection) |

### Invoice screen integration

The billing invoice detail page (`billing/frontend/pages/invoices/[id]/index.vue`)
conditionally shows GST labels for Indian clinics:

- **Tax totals line**: shows "GST" instead of "Tax" when
  `isIndianClinic` is true (checks `clinic.country == 'IN'` or
  `clinic.settings.country == 'IN'`).
- **Per-item VAT label**: shows "GST" instead of "VAT" for each line
  item's rate display.

---

## 13. Testing

### Backend tests

```bash
# Run all india_gst backend tests
docker compose exec backend python -m pytest tests/modules/india_gst/ -v

# Run a specific test
docker compose exec backend python -m pytest tests/modules/india_gst/test_uninstall_guard.py -v
```

Backend test files:
- `test_gst_calculator.py` — tax split engine (intra/inter-state, odd
  cents, credit notes, zero-rate, multi-line totals, FY document
  numbering)
- `test_hook_issue.py` — hook integration (intra/inter-state issue,
  missing place of supply, non-regular registration, re-issue
  idempotency)
- `test_uninstall_guard.py` — uninstall guard (blocked when issued
  invoices have GST data, allowed when no issued GST invoices)
- `test_settings_router.py` — settings CRUD, GSTIN validation, SAC
  defaults, autoconfigure, missing SAC translations
- `test_tax_preview_endpoint.py` — tax preview API
- `test_reports_service.py` — reconciliation report totals
- `test_einvoice_scaffolding.py` — e-invoice retry returns 409

### Frontend tests

```bash
# Run all india_gst frontend tests
docker compose exec frontend npx vitest run tests/india_gst/
```

Frontend test files:
- `tests/india_gst/useIndiaGstStates.test.ts` — state code/name mapping,
  options format, count verification
- `tests/india_gst/gstBadgeLogic.test.ts` — badge logic (Indian clinic
  detection, non-draft detection, severity colors, e-invoice labels,
  tooltip fallbacks, missing GST warning)

---

## 14. Troubleshooting

### "GST not showing on invoice"

The hook only runs on the `draft → issued` transition. If the invoice
was issued **before** india_gst was installed (or before the clinic's
country was set to `IN`), no GST data exists.

The invoice cannot retroactively enter GST after issuance. Workaround:
emit a credit note referencing the original, then issue a new invoice
with the same items — the hook will fire normally.

### "Cannot uninstall india_gst"

The uninstall guard blocks removal if any non-draft invoice has GST
line-item data. To uninstall:

1. Void or credit-note all issued invoices with GST data.
2. Retry uninstall from `Admin → Modules`.

### "Place of supply validation error on issue"

The hook requires `place_of_supply` to be set for regular registration
type. Set it in the GST panel on the draft invoice before issuing.

### "GSTIN validation fails"

GSTIN must match the CBIC format: `^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$`.
Example: `33ABCDE1234F1Z5`. The first two digits must be a valid state
code from `constants.INDIA_STATES`.

### "Tamil PDF shows boxes/squares"

Tamil characters require the `Noto Sans Tamil` font. Ensure
`fonts-noto-core` is installed in the backend Docker image (already in
the Dockerfile). After rebuilding:

```bash
docker compose up -d --build backend
```

### "GST labels showing for non-Indian clinics"

This is typically a frontend caching/HMR issue. Restart the frontend
container:

```bash
docker compose restart frontend
```

---

## 15. Known limitations & roadmap

### v1 limitations

- **Only `regular` registration type** computes GST. Composition,
  unregistered, and exempt are stored settings with no tax calculation.
- **E-invoice is scaffolding only.** No live GSP/IRP provider — the
  retry endpoint always returns 409.
- **No GSTR-1 filing export.** The CSV export is a reconciliation aid,
  not a validated statutory filing artifact.
- **No reverse charge mechanism.** RCM is out of scope for v1.
- **No TDS/TCS support.** Tax deducted/collected at source is not
  handled.

### Roadmap

- [ ] E-invoice provider adapter (GSP/IRP integration)
- [ ] Composition scheme tax calculation
- [ ] GSTR-1 compliant export format
- [ ] Reverse charge mechanism (RCM) support
- [ ] TDS/TCS handling
- [ ] Multi-GSTIN support (one clinic, multiple state registrations)
- [ ] Invoice-level SAC override (currently catalog-level only)

---

## References

- [GST Act 2017](https://www.gst.gov.in/)
- [CBIC GSTIN structure](https://www.gst.gov.in/help/registration)
- [SAC codes for services](https://www.gst.gov.in/sacodeservices)
- `docs/adr/0001-modular-plugin-architecture.md` — module boundary
- `docs/adr/0003-event-bus-over-direct-imports.md` — why this module
  uses the synchronous compliance hook instead of the event bus
- `CLAUDE.md` — developer reference for module internals
- `CHANGELOG.md` — version history
