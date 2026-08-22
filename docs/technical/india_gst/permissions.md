---
module: india_gst
last_verified_commit: 0000000
---

# India GST — permissions

> _Scaffolded stub — replace with proper documentation when this module is next touched._

Returned by `IndiaGstModule.get_permissions()`
(relative names; the registry namespaces them as `india_gst.<name>`).

| Permission | Allows | Required by |
|------------|--------|-------------|
| `india_gst.settings.read` | Read the clinic's GST profile (GSTIN, registration type, state, e-invoice config) | `GET /india_gst/settings`, `POST /india_gst/tax-preview`, `GET /india_gst/invoices/{id}/einvoice` |
| `india_gst.settings.configure` | Edit the clinic's GST profile | `PUT /india_gst/settings`, `POST /india_gst/invoices/{id}/einvoice/retry` |
| `india_gst.catalog.manage` | Read/edit SAC code defaults per treatment | `GET/PUT /india_gst/catalog-defaults` |
| `india_gst.reports.read` | View GST reconciliation reports and export | `GET /india_gst/reports/*` |

Editing GST fields on a *draft* invoice (`PUT /india_gst/invoices/{id}`)
reuses billing's own `billing.write` — it's billing-owned invoice data,
not a india_gst-specific concern.

## Role assignment

See `backend/app/core/auth/permissions.py` for the canonical role table.
`india_gst`'s own `role_permissions` grants `admin: ["*"]`,
`dentist`/`receptionist`: `["reports.read", "settings.read"]`,
`hygienist`/`assistant`: `["settings.read"]` — `settings.read` goes to
every clinical role because the invoice form/detail panels call
tax-preview and e-invoice status mid-invoicing.

## Adding a new permission

1. Add the relative name to `get_permissions()` in
   `backend/app/modules/india_gst/__init__.py`.
2. Add the namespaced form to the relevant role(s) in
   `manifest["role_permissions"]`.
3. Add a row to the table above.
4. Annotate the endpoint(s) with `Depends(require_permission(...))`.
5. Update `frontend/app/config/permissions.ts` if it gates UI.
