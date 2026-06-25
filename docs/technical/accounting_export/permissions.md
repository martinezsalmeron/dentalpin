# accounting_export — permissions

Namespaced from `get_permissions()` by the registry. Admin-only by
default (`role_permissions` grants `admin: ["*"]` and no other role).

| Permission                      | Gates | Endpoints |
|---------------------------------|-------|-----------|
| `accounting_export.export.read` | View the export page and preview counts/totals/sample | `GET /api/v1/accounting_export/preview` |
| `accounting_export.export.run`  | Generate and download the ZIP export | `GET /api/v1/accounting_export/run` |

Frontend references via `PERMISSIONS.accountingExport.read` /
`PERMISSIONS.accountingExport.run` (`frontend/app/config/permissions.ts`).
The navigation entry is gated on `accounting_export.export.read`.
