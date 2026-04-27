# Catalog module

Treatment catalog, categories, VAT types. Foundational pricing source
of truth for budgets and billing.

## Public API

Routes mounted at `/api/v1/catalog/`.

## Dependencies

`manifest.depends = []`. Foundational.

## Permissions

`catalog.read`, `catalog.write`, `catalog.admin`.

## Events emitted

None.

## Events consumed

None.

## Lifecycle

- `removable=False`. Budget, billing, odontogram, treatment_plan all
  depend on this.

## Gotchas

- **VAT types are versioned** — when changing a VAT rate, create a new
  version rather than mutating in place. Historical invoices must
  reproduce their original VAT.
- **Pricing rules live in `pricing.py`** — keep service code thin and
  delegate calculations there.
- **Seed data** is shipped via `seed.py` and idempotent — re-running it
  must not duplicate categories.

## Related ADRs

- `docs/adr/0001-modular-plugin-architecture.md`

## CHANGELOG

See `./CHANGELOG.md`.
