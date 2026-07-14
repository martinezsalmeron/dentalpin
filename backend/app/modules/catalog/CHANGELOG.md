# Changelog — catalog module

## Unreleased

- i18n: add French translations to seed data (Moroccan VAT rates).

- feat(tools): expose `list_catalog_items` + `get_catalog_item` READ
  agent tools (wrap `CatalogService`) so the copilot can read the
  treatment catalog — name, code, category, price, duration, scope.

- feat(seed): cover advanced surgical, periodontal and orthodontic
  techniques that any modern Spanish clinic offers and the Gesdén
  importer was previously dumping into ``Importado de Gesdén``. New
  catalog items: ``SURG-PRP`` (Plasma rico en plaquetas / PRGF),
  ``SURG-PERIIMP`` (tratamiento de periimplantitis), ``SURG-BONE-VERT``
  + ``SURG-BONE-HORIZ`` (aumento óseo vertical y horizontal),
  ``SURG-SINUS-CLOSED`` (elevación de seno cerrada / atraumática),
  ``PERIO-GINGIV`` (gingivectomía), ``PERIO-SURG-RESECT`` +
  ``PERIO-SURG-REGEN`` (cirugía periodontal resectiva y regenerativa),
  ``ORTO-TAD`` (microtornillo / anclaje esquelético temporal),
  ``ENDO-APICOFORM`` (apicoformación), ``PED-SPACE-COMPOUND``
  (mantenedor de espacio compuesto). Renames ``PED-FILL-TEMP`` from
  "Obturación en pieza temporal" to "Obturación en dentición
  temporal" — the standard Spanish wording, disambiguates from
  ``REST-TEMP`` (temporary filling material on any tooth).
- feat(seed): broaden coverage for Gesdén imports — add 36 treatments
  across diagnóstico (urgencia, segunda opinión, telerradiografía),
  preventivo (tartrectomía con curetaje, profilaxis infantil),
  restauradora (reconstrucción amplia, recementado de corona, corona
  sobre endodonciado, pilares de cicatrización/definitivo, reparación
  de obturación), endodoncia (apertura cameral urgente, recambio
  medicación, endo en temporal), periodoncia (curetaje por sextante,
  estudio periodontal, férula post-RAR), cirugía (injerto conectivo,
  alargamiento coronario, exéresis de quiste, exodoncia de incluido,
  regularización ósea), ortodoncia (cementado / descementado de
  bracket, separadores, expansor palatino), estética (reconstrucción
  estética, eliminación de pigmentación), prótesis (provisional
  removible, ajuste oclusal), odontopediatría (extracción / obturación
  en temporal, pulpectomía). Lifts the seed from 82 to 118 items so
  the migration_import fuzzy matcher finds a real destination instead
  of dumping treatments in ``Importado de Gesdén``.
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
