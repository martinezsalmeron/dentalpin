# Changelog — catalog module

## Unreleased

- feat(seed): add catalog items for implant-supported crowns —
  ``REST-CROWN-IMPL-MC`` (metal-ceramic), ``REST-CROWN-IMPL-ZIR``
  (zirconia) and ``REST-CROWN-IMPL-PROV`` (provisional). They map to
  the new odontogram clinical types ``crown_on_implant`` and
  ``provisional_crown_on_implant``.
- feat(sessions): new ``CatalogItemSession`` entity defines named,
  priced steps for treatments billed in stages (e.g. crown: "Toma de
  medidas" 200€ + "Colocación" 600€). Sum of session prices must
  equal the item ``default_price`` (422 on mismatch). Updates replace
  the template atomically. Migration ``cat_0003`` adds the table.
  Frontend admin ``CatalogItemModal`` gets a "Sesiones" section with
  editor + sum-validation chip.
- perf(list): ``CatalogService.list_items`` now counts directly via
  ``COUNT(TreatmentCatalogItem.id)`` instead of materialising the
  joined data query as a subquery.
- fix(isolation): drop the cross-module imports of
  ``billing.InvoiceItem`` and ``budget.BudgetItem`` from
  ``CatalogService.get_popular_items``. Catalog is foundational
  (``manifest.depends = []``) — importing consumer-module models
  inverted the DAG and blocked uninstall of billing / budget. The
  usage ranking now reads the sibling tables through a single raw
  ``UNION ALL`` SQL fragment and falls back to the most recent
  active items when a clinic has no budgets / invoices yet.
- Added per-module `CLAUDE.md` for AI-agent context (2026-04-27).

## 0.1.0 — initial

- Treatment catalog with categories.
- VAT types with versioning.
- Pricing rules in `pricing.py`.
- Idempotent seed in `seed.py`.
