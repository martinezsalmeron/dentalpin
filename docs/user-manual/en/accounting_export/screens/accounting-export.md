---
module: accounting_export
screen: export
route: /accounting-export
related_endpoints:
  - GET /api/v1/accounting_export/preview
  - GET /api/v1/accounting_export/run
related_permissions:
  - accounting_export.export.read
  - accounting_export.export.run
related_paths:
  - backend/app/modules/accounting_export/frontend/pages/accounting-export.vue
  - backend/app/modules/accounting_export/router.py
last_verified_commit: 0f7fa8c
---

# Accountant export

Generate the period's invoice and payment file to send to your
accountant.

## How to use it

> Viewing and previewing requires `accounting_export.export.read`.
> Downloading requires `accounting_export.export.run`.

1. Pick the **period** in the dropdown: *current month*, *previous
   month*, *current quarter*, *previous quarter*, *year to date*, or
   *custom* (with from/to dates).
2. Click **Preview**. You'll see the invoice and payment counts, the
   totals (base and total), and a sample of the first rows.
3. Click **Download (.zip)**. A ZIP with `facturas.csv` and `cobros.csv`
   is downloaded.

## What the file contains

- Only **issued invoices** (drafts are not exported) and the **payments
  allocated** to them.
- The CSV files use a semicolon (`;`) separator and comma decimals, with
  UTF-8 (BOM) encoding, so Spanish Excel opens them with correct accents
  and amounts.

## Permissions

| What you see / can do | Permission |
|-----------------------|------------|
| View the page and preview | `accounting_export.export.read` |
| Download the export (ZIP) | `accounting_export.export.run` |

## Troubleshooting

- **The menu entry is missing.** The module is optional: an admin must
  enable it from the module administration.
- **Expected payments are missing.** Only payments allocated to an
  invoice are exported. A standalone payment with no invoice is excluded
  by design.
- **The period comes back empty.** Check that there are **issued**
  invoices (not drafts) with an issue date inside the selected range.
