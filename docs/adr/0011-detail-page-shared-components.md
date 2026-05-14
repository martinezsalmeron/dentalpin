# 0011 — Detail-page shared components

- **Status:** accepted
- **Date:** 2026-05-13
- **Deciders:** Ramon Martinez (frontend)
- **Tags:** frontend, ui, design-system

## Context

Budget detail (`backend/app/modules/budget/frontend/pages/budgets/[id].vue`)
and invoice detail
(`backend/app/modules/billing/frontend/pages/invoices/[id]/index.vue`)
had grown two parallel implementations of the same UI structure:
page header with title + status chips, action bar with overflow,
totals card, sidebar metadata card.

The two implementations had drifted: invoice header used a no-wrap
`flex` container (chips overlapped on mobile), had 8 inline buttons
with no overflow grouping, and inlined a status→colour map already
present in `frontend/app/config/severity.ts`. Budget had been
redesigned with mobile-first patterns but didn't ship reusable
primitives. Any new "document" detail page (rectificativa, recibo,
treatment-plan view) would copy whichever was closer.

We already had the right substrate:
`frontend/app/config/severity.ts` (semantic roles + entity status
maps), `frontend/app/components/shared/StatusBadge.vue` (semantic
badge), `frontend/app/composables/useBreakpoint.ts` and
`useCurrency.ts`. What was missing were a few wrapper components and
a composable that bind them to the per-entity context.

## Decision

All "detail" pages (budget, invoice, future documents) render through
a fixed set of shared components living under
`frontend/app/components/shared/`:

- `DetailPageHeader`
- `EntityStatusChips`
- `EntityActionBar`
- `EntityTotalsCard`
- `EntityInfoCard`
- `EntityCriticalBanner`

…and a single composable `useEntityStatus` that maps a status string
to `{ role, label, uiColor }` using the entity maps already declared
in `severity.ts`.

Status→colour maps live in `severity.ts` only. Status→label
translations live in i18n only. No module-local colour maps, no
inline `getXxxBadgeColor()` helpers, no hardcoded chip arrays in
templates.

## Consequences

### Good

- One place to fix bugs in chip wrapping, focus styles, action
  collapsing, etc.
- Compliance modules (Verifactu and future country-specific ones)
  have a stable contract: inject a chip via the existing slot, or a
  banner via `EntityCriticalBanner`. No need to touch billing.
- New document detail pages have a ~30-line template instead of
  ~1000.
- Visual language is enforced by code, not by reviewer vigilance.

### Bad / accepted trade-offs

- One more indirection between the page and the markup; reading a
  detail page now requires opening 2–3 component files to understand
  the visual output.
- The shared components live in `frontend/app/components/shared/`,
  which is a host-level directory consumed by module layers. A future
  module that wanted to ship its own detail page from outside the
  monorepo would need access to these primitives (acceptable: our
  modules ship as Nuxt layers under the same workspace).

## Alternatives considered

- **Leave both pages as-is, fix invoice in-place.** Cheapest but
  guarantees the drift continues; the next document we add (credit
  note, payment receipt) starts from yet another copy.
- **Build a heavyweight "DocumentPage" component that owns the whole
  layout including main content.** Too rigid — the body of each
  detail page diverges (items vs. payments vs. compliance) and
  forcing a single template would push module-specific logic into
  shared/.
- **Use Nuxt UI v4's `<UPageHeader>` directly.** It doesn't cover
  status chips, version pill, or the responsive action collapsing we
  need; would still require wrappers.

## How to verify the rule still holds

- Grep: `rg "getStatusBadgeColor|getStatusColor" backend/app/modules/*/frontend/`
  must return zero results (after migration PRs land).
- Grep: `rg "<h1[^>]*>" backend/app/modules/*/frontend/pages/**/[id]*`
  should match only files that immediately enclose the title inside
  `<DetailPageHeader>`.
- Tests: `frontend/tests/composables/useEntityStatus.test.ts` covers
  the role/label/uiColor contract; expand component tests as
  components evolve.

## References

- `frontend/app/components/shared/DetailPageHeader.vue`
- `frontend/app/components/shared/EntityStatusChips.vue`
- `frontend/app/components/shared/EntityActionBar.vue`
- `frontend/app/components/shared/EntityTotalsCard.vue`
- `frontend/app/components/shared/EntityInfoCard.vue`
- `frontend/app/components/shared/EntityCriticalBanner.vue`
- `frontend/app/composables/useEntityStatus.ts`
- `frontend/app/config/severity.ts`
- `docs/technical/detail-page-shared-components.md`
