# Billing module

Invoices, payments, credit notes, PDF generation.

## Public API

Routes mounted at `/api/v1/billing/`.

## Dependencies

`manifest.depends = ["patients", "catalog", "budget"]`.

## Permissions

`billing.read`, `billing.write`, `billing.admin`.

## Events emitted

- `invoice.issued`
- `invoice.sent`
- `invoice.paid`

## Events consumed

- _none today_. The legacy ``budget.completed`` subscription was
  removed in 2026-04 — that event was never actually published, so
  the handler was orphaned. Re-add a subscription here when invoices
  need to react to budget lifecycle events again.

## Lifecycle

- `removable=False`. Fiscal data has legal retention (see verifactu
  module for AEAT specifics).

## Gotchas

- **Compliance hooks live in compliance modules**, not here. The
  `verifactu` module attaches via `BillingComplianceHook` on
  `invoice.issued` to chain into AEAT. Don't import verifactu from
  billing — the relation is via hooks + events.
- **PDF generation uses WeasyPrint** (`pdf.py`). Requires the system
  fonts present in the production image.
- **Credit notes** are issued via the same workflow as invoices,
  flagged via the document type. Don't introduce a parallel pipeline.

## Related ADRs

- `docs/adr/0001-modular-plugin-architecture.md`
- `docs/adr/0003-event-bus-over-direct-imports.md`

## CHANGELOG

See `./CHANGELOG.md`.
