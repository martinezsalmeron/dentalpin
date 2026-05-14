---
module: shared
last_verified_commit: 74a12b8
---

# Lists redesign — technical plan

Companion to [`docs/features/lists-redesign.md`](../features/lists-redesign.md) (UX spec). Cross-module payments endpoints have their own contract at [`./payments/cross-module-summaries.md`](./payments/cross-module-summaries.md). This file is the engineering contract for **the four list pages and the shared primitives layer**.

## Goal

Ship a single PR that:

1. Lands a reusable list/filter primitives layer in host `frontend/`.
2. Upgrades `/patients`, `/budgets`, `/invoices`, `/payments` to consume that layer with the columns and filters the UX brief calls for.
3. Adds the four payments-side endpoints that let the cross-module slots filter and enrich without violating module isolation.
4. Adds URL-state sync (filters + page + sort) via a shared composable.
5. Renders mobile-first (card view <md, slide-over filters).

Zero manifest changes. Zero new permissions. Zero migrations. Zero off-books exposure.

## Architecture audit (verified against `feat/payments-module`)

| Claim | Verified |
|---|---|
| `patients.depends = []` | `backend/app/modules/patients/CLAUDE.md` |
| `budget.depends = ["patients", "catalog", "odontogram"]` — does **not** include payments | `backend/app/modules/budget/CLAUDE.md` |
| `payments.depends = ["patients", "budget"]` | `backend/app/modules/payments/__init__.py:46` |
| `billing.depends = ["patients", "catalog", "budget", "payments"]` | `backend/app/modules/billing/__init__.py:31`. Billing imports `Payment` and `Refund` models (`billing/service.py:11-12`), legal per its `depends`. |
| Slot registry filters by permission + condition | `frontend/app/composables/useModuleSlots.ts:94-108` |
| `<ModuleSlot>` passes ctx verbatim to each registered component | `frontend/app/components/ModuleSlot.vue` |
| Provider self-registration pattern is in use | `backend/app/modules/payments/frontend/plugins/slots.client.ts` (3 slots already registered: `budget.detail.sidebar`, `reports.categories`, `patient.detail.administracion.payments`) |
| Existing list-toolbar slot precedent (extensibility on a list page) | `backend/app/modules/billing/frontend/pages/invoices/index.vue:179` registers `invoice.list.toolbar.filters` ctx |
| Existing list-row slot precedent | `backend/app/modules/billing/frontend/pages/invoices/index.vue:247` registers `invoice.list.row.meta` ctx |
| Patient debt is off-books safe | `LedgerService.get_patient_ledger` `backend/app/modules/payments/service.py:149-198` → `clinic_receivable = max(0, total_earned − net_paid)`. Pure payments-axis. |
| Budget collected is off-books safe | `PaymentReadService.total_collected_for_budget` `backend/app/modules/payments/service.py:128-139` → `Σ PaymentAllocation.amount where target_type='budget'`. Pure payments-axis. |
| `do_not_contact` flag exists on Patient | `backend/app/modules/patients/CLAUDE.md` gotchas |
| `PaginatedApiResponse[T]` is the standard list response shape | `backend/app/core/schemas.py` |
| Existing list primitives | `frontend/app/components/shared/{ListRow,SearchBar,PaginationBar,EmptyState,FilterChip,StatusBadge,Money,PageHeader}.vue` |
| `BudgetStatus` enum | `frontend/app/types` exports `BudgetStatus` = `'draft' \| 'sent' \| 'accepted' \| 'completed' \| 'rejected' \| 'expired' \| 'cancelled'` (note: `'completed'` was deprecated 2026-04 but the union still includes it) |
| `InvoiceStatus` enum | `'draft' \| 'issued' \| 'partial' \| 'paid' \| 'cancelled' \| 'voided'` |
| `PaymentMethod` enum | `'cash' \| 'card' \| 'bank_transfer' \| 'direct_debit' \| 'insurance' \| 'other'` |

## Cross-module data flow (no dependency violations)

```
                    ┌─────────────────────┐
                    │  /patients page     │  (patients module)
                    │  /budgets page      │  (budget module)
                    │                     │
                    │  [native cols]      │  [slot: row.financial / row.payments]
                    │  [native filters]   │  [slot: filter chip]
                    │                     │
                    │   ▲ permission-gated, falls back to empty when payments
                    │   │ is uninstalled or user lacks payments.record.read
                    └──┴──────────────────┘
                          │ slot ctx { patient_id | budget_id, summary }
                          ▼
                    ┌─────────────────────┐
                    │  payments module    │  registers slot fillers in
                    │  (frontend layer)   │  frontend/plugins/slots.client.ts
                    │                     │
                    │  hits its own       │
                    │  /api/v1/payments/  │
                    │  endpoints          │
                    └─────────────────────┘
```

Server-side flow when a user picks "Cobro: Sin pagar" in `/budgets`:

```
useListQuery (budgets page)
   │ filters.payment_status = "unpaid"
   ▼
1. GET /api/v1/payments/filters/budgets-by-status?status=unpaid
       → { budget_ids: [...], truncated: false }
2. GET /api/v1/budget/budgets?budget_ids=<intersect>&page=1&...
       → PaginatedApiResponse<BudgetListResponse>
3. POST /api/v1/payments/summary/by-budgets { budget_ids: [page items] }
       → { [id]: { collected, pending, payment_status } }   (slot consumes)
```

The budget endpoint never reaches into payments — it just accepts an extra `budget_ids` filter. Payments owns both the filter set and the per-row summary. Identical pattern for `/patients` + "Con deuda > 0".

## File map

### A. New primitives — host `frontend/`

| Path | Purpose |
|---|---|
| `frontend/app/components/shared/DataListLayout.vue` | Page wrapper: header + toolbar slot + body slot + footer. Handles loading/empty/error states. |
| `frontend/app/components/shared/DataListItem.vue` | Row wrapper exposing `row` (md+) and `card` (<md) slots; switch via Tailwind `hidden md:flex` / `flex md:hidden`. Wraps existing `ListRow` for the row variant. |
| `frontend/app/components/shared/FilterBar.vue` | Horizontal chips container + "Filtros (N)" button opening `USlideover` on mobile or popover on desktop. |
| `frontend/app/components/shared/FilterChipMulti.vue` | Multi-select dropdown chip. Label updates "Estado" → "Estado · 2". |
| `frontend/app/components/shared/FilterDateRange.vue` | Date range with preset chips (Hoy / 7d / 30d / Este mes / Trimestre / Año / Personalizado). |
| `frontend/app/components/shared/FilterToggle.vue` | Boolean chip. On/off + optional tri-state. |
| `frontend/app/components/shared/FilterEntityPicker.vue` | Async autocomplete picker. Takes a `fetcher: (q: string) => Promise<Option[]>`. Used for patient, professional, series, distinct cities. |
| `frontend/app/components/shared/SortMenu.vue` | Dropdown with `{ field, dir }` options. Emits canonical `field:asc` string. |
| `frontend/app/composables/useListQuery.ts` | The composable. URL ↔ state sync + debounced fetch. Contract below. |

### B. Backend primitives

| Path | Purpose |
|---|---|
| `backend/app/core/list_query.py` | Helper to parse `?sort=field:dir` into `(column, direction)` against an allow-list; pagination dataclass; `ids` list parser with cap. |

### C. New backend endpoints (payments)

All four documented in detail in [`./payments/cross-module-summaries.md`](./payments/cross-module-summaries.md). Summary:

| Method | Path | Permission |
|---|---|---|
| POST | `/api/v1/payments/summary/by-budgets` | `payments.record.read` |
| POST | `/api/v1/payments/summary/by-patients` | `payments.record.read` |
| GET | `/api/v1/payments/filters/budgets-by-status` | `payments.record.read` |
| GET | `/api/v1/payments/filters/patients-with-debt` | `payments.record.read` |

### D. Backend endpoint upgrades (existing modules)

| File | Change |
|---|---|
| `backend/app/modules/patients/router.py` `list_patients` | Add query params: `patient_ids: list[UUID] \| None`, `city: str \| None`, `do_not_contact: bool \| None`, `sort: str \| None` (allow-list: `last_name`, `created_at`). |
| `backend/app/modules/patients/service.py` `PatientService.list_patients` | Apply new filters; honor `patient_ids` via `Patient.id.in_(...)`; sort via `core.list_query.apply_sort()`. |
| `backend/app/modules/budget/router.py` `list_budgets` | Add `budget_ids: list[UUID] \| None`, `assigned_professional_id: UUID \| None`, `valid_until_before: date \| None`, `valid_until_after: date \| None`, `sort: str \| None` (allow-list: `created_at`, `valid_until`, `total_with_tax`). |
| `backend/app/modules/budget/service.py` `BudgetService.list_budgets` | Apply new filters + sort. |
| `backend/app/modules/billing/router.py` `list_invoices` | Add `sort: str \| None` (allow-list: `issue_date`, `due_date`, `total`, `balance_due`). |
| `backend/app/modules/billing/service.py` `InvoiceService.list_invoices` | Apply sort. (Backend already sorts paginated results by `created_at`; switch to dynamic.) |
| `backend/app/modules/payments/router.py` `list_payments` | Add `has_refunds: bool \| None`, `has_unallocated: bool \| None`, `amount_min: Decimal \| None`, `amount_max: Decimal \| None`, `sort: str \| None` (allow-list: `payment_date`, `amount`). |
| `backend/app/modules/payments/service.py` `PaymentService.list` | Apply new filters + sort. |

No schema changes. No migrations.

### E. Modified frontend pages

| Path | Change |
|---|---|
| `backend/app/modules/patients/frontend/pages/patients/index.vue` | Rewrite the body around `<DataListLayout>` + `<FilterBar>` + `<DataListItem>`. Replace `useAsyncData` with `useListQuery<PatientListFilters>()`. Render slot `patients.list.row.financial` per row, slot `patients.list.filter` in toolbar. |
| `backend/app/modules/budget/frontend/pages/budgets/index.vue` | Same shell. Render slots `budget.list.row.payments` per row, `budget.list.filter` in toolbar. Move PDF download + delete to row `actions` slot. Add city/professional filters. |
| `backend/app/modules/billing/frontend/pages/invoices/index.vue` | Same shell. Preserve existing `invoice.list.row.meta` + `invoice.list.toolbar.filters` slots. Add SortMenu. Add date-range filter to main bar. |
| `backend/app/modules/payments/frontend/pages/payments/index.vue` | Same shell. Replace the 4-col grid with `<FilterBar>`. Replace the patient-id text input with `<FilterEntityPicker>`. Add SortMenu + pagination UI. |

### F. Modified composables

| Path | Change |
|---|---|
| `backend/app/modules/budget/frontend/composables/useBudgets.ts` | Extend `BudgetListParams` with `budget_ids`, `assigned_professional_id`, `valid_until_before`, `valid_until_after`, `sort`. URLSearchParams loop. |
| `backend/app/modules/billing/frontend/composables/useInvoices.ts` | Extend `InvoiceListParams` with `sort`. |
| `backend/app/modules/payments/frontend/composables/usePayments.ts` | Extend `PaymentListParams` with `has_refunds`, `has_unallocated`, `amount_min`, `amount_max`, `sort`. Add `fetchBudgetSummaries(ids)`, `fetchPatientDebtSummaries(ids)`, `fetchBudgetIdsByPaymentStatus(status)`, `fetchPatientIdsWithDebt(min_debt)`. |
| `backend/app/modules/patients/frontend/composables/usePatients.ts` (NEW — mirrors `useBudgets`) | List params interface + `fetchPatients`. Replace the `useAsyncData` pattern in the page. |

### G. Slot registrations — payments module

Edit `backend/app/modules/payments/frontend/plugins/slots.client.ts` to add four registrations:

```ts
// Patients list — debt badge per row
registerSlot('patients.list.row.financial', {
  id: 'payments.patients.list.row.debt',
  component: defineAsyncComponent(() => import('../components/PatientListDebtCell.vue')),
  permission: 'payments.record.read',
  order: 10
})

// Patients list — "Con deuda" filter chip
registerSlot('patients.list.filter', {
  id: 'payments.patients.list.filter.withDebt',
  component: defineAsyncComponent(() => import('../components/PatientListDebtFilter.vue')),
  permission: 'payments.record.read',
  order: 10
})

// Budgets list — collected/pending mini progress per row
registerSlot('budget.list.row.payments', {
  id: 'payments.budget.list.row.collected',
  component: defineAsyncComponent(() => import('../components/BudgetListPaymentsCell.vue')),
  permission: 'payments.record.read',
  order: 10
})

// Budgets list — payment-status filter chip
registerSlot('budget.list.filter', {
  id: 'payments.budget.list.filter.paymentStatus',
  component: defineAsyncComponent(() => import('../components/BudgetListPaymentsFilter.vue')),
  permission: 'payments.record.read',
  order: 10
})
```

### H. New components — payments module

| Path | Purpose |
|---|---|
| `backend/app/modules/payments/frontend/components/PatientListDebtCell.vue` | Renders the debt badge per row. Receives `ctx = { patient_id, summary }`. If `summary == null` the page parent hasn't returned a value for this id (paciente sin actividad) — render nothing. |
| `backend/app/modules/payments/frontend/components/PatientListDebtFilter.vue` | Toggle "Con deuda > 0". Emits via `ctx.onChange`. |
| `backend/app/modules/payments/frontend/components/BudgetListPaymentsCell.vue` | Mini progress + status chip per row. Receives `ctx = { budget_id, summary }`. |
| `backend/app/modules/payments/frontend/components/BudgetListPaymentsFilter.vue` | Multi-select chip "Cobro" (Pagado/Parcial/Sin cobro). |

## `useListQuery<TFilters>()` contract

```ts
import { useRoute, useRouter } from '#imports'

export interface ListQueryConfig<TFilters> {
  /** Default filter state when URL is empty. */
  defaults: TFilters
  /** URL ↔ filter codec: defines query-param name, type, parse, serialize. */
  schema: ListQuerySchema<TFilters>
  /** Default page size. */
  pageSize: number
  /** Allowed sort fields with their server-side spelling. */
  sortable: readonly string[]
  /** Default sort. e.g. `'created_at:desc'`. */
  defaultSort: string
  /** Debounce ms for text-search field. Default 300. */
  searchDebounce?: number
  /** The fetcher. Receives the resolved query and returns the API response. */
  fetcher: (query: ResolvedQuery<TFilters>) => Promise<{ data: unknown[]; total: number }>
}

export interface ResolvedQuery<TFilters> {
  filters: TFilters
  page: number
  pageSize: number
  sort: string  // 'field:asc' | 'field:desc'
}

export interface UseListQueryReturn<TFilters, TRow> {
  filters: Ref<TFilters>
  page: Ref<number>
  pageSize: Ref<number>
  sort: Ref<string>
  rows: Ref<TRow[]>
  total: Ref<number>
  isLoading: Ref<boolean>
  error: Ref<string | null>
  setFilter: <K extends keyof TFilters>(k: K, v: TFilters[K]) => void
  resetFilters: () => void
  refresh: () => Promise<void>
}

export function useListQuery<TFilters extends Record<string, unknown>, TRow>(
  cfg: ListQueryConfig<TFilters>
): UseListQueryReturn<TFilters, TRow>
```

### URL serialization rules

| Filter shape | URL form |
|---|---|
| `string` (search) | `?q=lopez` (debounced 300 ms before push) |
| `string[]` (multi-select) | `?status=draft,accepted` |
| `boolean` | `?overdue=1` (omitted if false) |
| `boolean \| null` (tri-state) | `?do_not_contact=1` / `?do_not_contact=0` / omitted |
| Date range | `?date_from=2026-01-01&date_to=2026-03-31` |
| Date range preset | `?date_preset=this_month` (mutually exclusive with explicit from/to) |
| UUID list | `?patient_ids=<comma-separated>` |
| Number range | `?amount_min=10&amount_max=100` |
| Page | `?page=2` (omitted when 1) |
| Sort | `?sort=valid_until:asc` (omitted when default) |

`useListQuery` writes the URL via `router.replace` (no history pollution from typing in search). Back/forward navigation rehydrates state.

### Cross-module filter resolution

`useListQuery` does NOT know about cross-module filters. The page's `fetcher` is responsible for translating `payment_status` / `with_debt` into a payments-side fetch + intersect:

```ts
// Inside the /budgets page fetcher
async function fetchBudgetsWithEnrichment(q: ResolvedQuery<BudgetListFilters>) {
  let budgetIdsIntersect: string[] | undefined
  if (q.filters.payment_status?.length) {
    const { budget_ids, truncated } = await payments.fetchBudgetIdsByPaymentStatus(
      q.filters.payment_status
    )
    budgetIdsIntersect = budget_ids
    if (truncated) toast.warning(t('lists.truncatedWarning'))
  }
  const list = await budgets.fetchBudgets({
    ...mapBudgetFilters(q.filters),
    budget_ids: budgetIdsIntersect,
    page: q.page,
    page_size: q.pageSize,
    sort: q.sort
  })
  // Fire-and-forget enrichment for slot consumption
  const summaries = await payments.fetchBudgetSummaries(list.map(b => b.id))
  budgetSummaries.value = summaries
  return { data: list, total: budgets.total.value }
}
```

The page passes `budgetSummaries.value[budget.id]` into `<ModuleSlot :ctx="{ budget_id: budget.id, summary }">` so the slot renders synchronously.

## `DataListLayout.vue` contract

```vue
<DataListLayout
  :title="t('budget.title')"
  :loading="isLoading"
  :error="error"
  :empty="!rows.length"
  :total="total"
  :page="page"
  :page-size="pageSize"
  @update:page="page = $event"
>
  <template #actions>...primary CTAs...</template>
  <template #toolbar>
    <FilterBar :filters="filters" :sort="sort" ...>
      <FilterChipMulti ... />
      <ModuleSlot name="budget.list.filter" :ctx="{ value, onChange }" />
    </FilterBar>
  </template>
  <template #empty>
    <EmptyState .../>
  </template>
  <template #row="{ row }">
    <DataListItem>
      <template #row>...desktop layout...</template>
      <template #card>...mobile layout...</template>
    </DataListItem>
  </template>
</DataListLayout>
```

Renders `<USkeleton>` rows on loading. Pagination via `PaginationBar`. Error via existing `<UAlert>` pattern.

## URL state migration

Existing pages today (especially patients) use `useAsyncData('patients:list', ...)` with `watch` on local refs. The migration is:

1. Remove the page's local `searchQuery`, `currentPage`, `selectedStatuses`, etc.
2. Instantiate `useListQuery<TFilters>(cfg)` once at page top.
3. Pass the returned reactive bag into `<DataListLayout>` + `<FilterBar>` slots.
4. Each filter chip binds `v-model:value` to `filters.X` via `setFilter`.

The composable is the single source of truth for the URL + the fetcher. No more `watch([currentPage, debouncedSearch, ...], loadX)`.

## Permission audit

| Read | Permission |
|---|---|
| `/patients` list | `patients.read` (existing) |
| `/budgets` list | `budget.read` (existing) |
| `/invoices` list | `billing.read` (existing) |
| `/payments` list | `payments.record.read` (existing) |
| Debt cell + filter (slot) | `payments.record.read` |
| Budget cobro cell + filter (slot) | `payments.record.read` |
| Summary endpoints + filter-ids endpoints | `payments.record.read` |

No new permissions in `get_permissions()`. No `role_permissions` changes.

## i18n keys (Spanish + English)

### Host `frontend/i18n/locales/{en,es}.json`

```jsonc
{
  "lists": {
    "filter": {
      "all": "Todos",
      "more": "Más filtros",
      "moreCount": "Más filtros ({count})",
      "clear": "Limpiar",
      "apply": "Aplicar"
    },
    "sort": {
      "label": "Ordenar",
      "asc": "Ascendente",
      "desc": "Descendente"
    },
    "datePreset": {
      "today": "Hoy",
      "last7": "Últimos 7 días",
      "last30": "Últimos 30 días",
      "thisMonth": "Este mes",
      "thisQuarter": "Trimestre",
      "thisYear": "Año",
      "custom": "Personalizado"
    },
    "truncatedWarning": "Resultados truncados a 1000; refina los filtros."
  }
}
```

### Per-module additions

| Module | Keys added |
|---|---|
| patients | `patients.filters.{withDebt, doNotContact, city, status}`, `patients.columns.{city, debt, contact}`, `patients.empty.{withFilters}` |
| budget | `budget.filters.{paymentStatus, professional, validity}`, `budget.columns.{collected, validUntil}`, `budget.paymentStatus.{paid, partial, unpaid}` |
| billing | `invoice.filters.{dateRange, series, isCreditNote, amountRange}`, `invoice.columns.{daysOverdue}` |
| payments | `payments.filters.{methodChips, hasRefunds, hasUnallocated}`, `payments.columns.{allocations}`, `payments.list.filterPatientPicker` |

## Implementation order (within the single PR)

1. **Primitives layer** (no business logic):
   - `DataListLayout.vue`
   - `DataListItem.vue`
   - `FilterBar.vue`
   - `FilterChipMulti.vue`
   - `FilterDateRange.vue`
   - `FilterToggle.vue`
   - `FilterEntityPicker.vue`
   - `SortMenu.vue`
   - `useListQuery.ts`
   - `app/core/list_query.py`
   - Story-level smoke component (optional `~/dev/lists-playground.vue` non-checked-in).
2. **Backend endpoint upgrades** (no list-page changes yet):
   - `/patients` accepts new params.
   - `/budgets` accepts new params.
   - `/invoices` accepts `sort`.
   - `/payments` accepts new params.
   - Four new endpoints in payments. Per-endpoint tests.
3. **Slot fillers in payments**:
   - 4 new components, 4 new `registerSlot` calls.
4. **Migrate the four pages**, one at a time, validating each before moving on:
   - `/patients`
   - `/budgets`
   - `/invoices`
   - `/payments`
5. **i18n + CHANGELOG** for every module touched.
6. **Screen MDs** bilingüe in `docs/user-manual/{en,es}/{patients,budget,billing,payments}/screens/<list>.md`.
7. **Smoke + tests + lint** (see below).

Each layer is independently mergeable in theory, but we ship them together to keep the user-facing change atomic.

## Test plan

### Backend

| Test | Where |
|---|---|
| `/patients?city=Madrid` returns only matching patients | `backend/tests/modules/patients/test_list.py` |
| `/patients?do_not_contact=true` returns the set with the flag | same |
| `/patients?patient_ids=<list>&page=...` intersects + paginates | same |
| `/patients?sort=last_name:asc` orders correctly; invalid sort returns 422 | same |
| `/budgets?budget_ids=<list>` intersects | `backend/tests/modules/budget/test_list.py` |
| `/budgets?assigned_professional_id=<uuid>` filters | same |
| `/budgets?valid_until_before=2026-06-01` filters | same |
| `/budgets?sort=valid_until:asc` orders | same |
| `/invoices?sort=balance_due:desc` orders | `backend/tests/modules/billing/test_invoice_list.py` |
| `/payments?has_refunds=true` filters | `backend/tests/modules/payments/test_list.py` |
| `/payments?has_unallocated=true` filters | same |
| `/payments?amount_min=100&amount_max=200` filters | same |
| New payments endpoints: see [`./payments/cross-module-summaries.md`](./payments/cross-module-summaries.md) | `backend/tests/modules/payments/test_cross_module_summaries.py` |
| **Off-books invariant**: build a patient with `earned > 0` and no invoice; assert `clinic_receivable` from ledger ≠ `Σ invoice.balance_due` (which is 0); assert the patients-list "with debt" filter includes this patient | new test |
| **Module isolation grep**: `from app.modules.payments` inside `backend/app/modules/{patients,budget}/` → 0 | CI / pre-merge script |

### Frontend

| Test | Where |
|---|---|
| `useListQuery` serializes filters to URL and rehydrates on mount | `frontend/test/composables/useListQuery.spec.ts` |
| Back/forward navigation reproduces filter state | same |
| `DataListItem` renders `row` slot ≥md, `card` slot <md | `frontend/test/components/shared/DataListItem.spec.ts` |
| FilterBar collapses to slide-over <md | manual visual + Playwright if time |
| Permission-revoked slot renders nothing | manual: revoke `payments.record.read`, expect zero debt column and zero "Con deuda" chip on `/patients` |

### Manual smoke

1. `docker-compose up`, `./scripts/reset-db.sh && ./scripts/seed-demo.sh`. Login `admin@demo.clinic`.
2. Walk through each of the 4 lists at 1280×800 and 375×667.
3. Apply each new filter; confirm URL updates; refresh; confirm state restored.
4. Confirm pagination across pages keeps filters.
5. Sort menu cycles through allowed fields + directions.
6. With a test patient that has `earned > 0` and no payments, `/patients` with "Con deuda" filter shows them; `/invoices` does not (no invoice exists).
7. With a budget that has 50% allocations, `/budgets` row shows the mini progress bar at ~50% and chip "Parcial".

### Lint + types

- `cd backend && ruff check . && ruff format --check .`
- `cd frontend && npm run lint`
- `docker-compose exec backend python -m pytest -v -k "list"`

## Performance considerations

- **Bulk summary endpoints capped at 100 ids per call** — the page size is 20–50, so a single call per page is plenty. Reject >100 with 422.
- **`filter-ids` endpoints capped at 1000 ids** with `truncated` flag. UI shows a toast warning. Realistic clinics rarely have 1000+ patients with debt or 1000+ unpaid budgets.
- **No N+1**: payments-side summaries use `Σ + group_by` once per call (see `service.py:total_collected_for_budget` precedent).
- **Indexes already in place**: `idx_payments_clinic_date`, `idx_payment_allocations_target` (assumed; verify during impl). If `PaymentAllocation.budget_id` lacks an index, add it in the payments module's own Alembic branch.

## Out of scope (explicit)

See the [UX brief](../features/lists-redesign.md#lo-que-esta-feature-no-añade). Recap: no SavedView model, no bulk actions, no swipe actions, no tags, no schedules slot, no CSV export, no column-header sort, no manifest changes, no new permissions, no migrations (except the optional index above).

## CHANGELOG entries

- `frontend/CHANGELOG.md` not required (host frontend has no per-module changelog).
- `backend/app/modules/patients/CHANGELOG.md` — `Added: Slots patients.list.row.financial and patients.list.filter; query params city, do_not_contact, patient_ids, sort`.
- `backend/app/modules/budget/CHANGELOG.md` — `Added: Slots budget.list.row.payments and budget.list.filter; query params budget_ids, assigned_professional_id, valid_until_before/after, sort`.
- `backend/app/modules/billing/CHANGELOG.md` — `Added: ?sort= on invoice list`.
- `backend/app/modules/payments/CHANGELOG.md` — `Added: summary/by-budgets, summary/by-patients, filters/budgets-by-status, filters/patients-with-debt endpoints; payments list params has_refunds, has_unallocated, amount_min/max, sort`.

## Cross-links

- UX brief: [`docs/features/lists-redesign.md`](../features/lists-redesign.md).
- Payments cross-module endpoints contract: [`./payments/cross-module-summaries.md`](./payments/cross-module-summaries.md).
- Documentation portal contract: [`./documentation-portal.md`](./documentation-portal.md).
- ADR 0001 modular architecture, ADR 0003 event bus over imports, ADR 0010 payments primitive.
- Module-creation guide: [`./creating-modules.md`](./creating-modules.md).
