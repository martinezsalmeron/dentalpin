# Reports module

Cross-module reporting: billing, budgets, scheduling.

## Public API

Routes mounted at `/api/v1/reports/`.

## Dependencies

`manifest.depends = ["patients", "agenda", "catalog", "budget", "billing"]`.
Read-only consumer of every business module.

## Permissions

`reports.billing.read`, `reports.budgets.read`,
`reports.scheduling.read`.

## Events emitted

None.

## Events consumed

None today — reports are computed on demand from underlying tables.

## Frontend slots exposed

| Slot | Ctx | Consumer |
|---|---|---|
| `reports.categories` | `{}` | `payments` adds the "Informe de cobros" card so the dashboard is discovered from `/reports` without a nav entry. Other modules may add more reports the same way. |

Reports never imports its slot consumers — the registry is the only
contract.

## Lifecycle

- `removable=False` — but a candidate for `removable=True` since this
  is a pure read-side module.

## Gotchas

- **Reads-only.** No writes from this module to other modules' tables.
- **Aggregations should be paginated and indexed.** Don't issue
  unbounded scans across multi-million-row tables.
- **Permissions are per-report-family.** Adding a new report =
  adding a new permission, registry-prefixed.

## Related ADRs

- `docs/adr/0001-modular-plugin-architecture.md`
- `docs/adr/0005-relative-permissions.md`

## CHANGELOG

See `./CHANGELOG.md`.
