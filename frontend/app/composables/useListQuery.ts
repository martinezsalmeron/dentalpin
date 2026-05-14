/**
 * useListQuery — shared list-page state with URL sync.
 *
 * The four list pages (/patients, /budgets, /invoices, /payments) share
 * the same shape:
 *   - text search (debounced)
 *   - typed filters
 *   - page + page_size
 *   - sort
 *   - fetcher that returns { data, total }
 *
 * URL is the source of truth: typing a filter rewrites the URL, opening
 * a saved link rehydrates the state, browser back/forward works.
 *
 * Filter encoding (built-ins):
 *   string         → ?key=value          (debounced when key === searchKey)
 *   string[]       → ?key=v1,v2,v3       (omitted when empty)
 *   boolean        → ?key=1              (omitted when false / null / undefined)
 *   null/undefined → key omitted
 *
 * Cross-module filters (e.g. ``with_debt``, ``payment_status``) live in
 * the same filters bag; the page's ``fetcher`` is responsible for
 * translating them into intersect calls on the payments module before
 * hitting its own list endpoint.
 */
import { computed, onBeforeUnmount, ref, watch, type Ref } from 'vue'
import { useRoute, useRouter } from '#imports'

export type FilterPrimitive = string | string[] | boolean | number | null | undefined
// Loose constraint — pages declare typed interfaces with concrete filter
// shapes; the composable handles values uniformly through ``serialize`` /
// ``parseInto`` which expect FilterPrimitive at runtime. The constraint
// stays ``object`` so concrete page-side ``interface XxxFilters {}``
// declarations remain assignable as generic args.
export type FiltersBag = object

export interface ResolvedQuery<F extends FiltersBag> {
  filters: F
  page: number
  pageSize: number
  sort: string
}

export interface ListQueryConfig<F extends FiltersBag, R> {
  /** Default filter state when the URL is empty. */
  defaults: F
  /** Page size (clamped 1–100). Default 20. */
  pageSize?: number
  /** Allowed sort fields. The frontend just enforces a closed set. */
  sortable: readonly string[]
  /** Default sort string, e.g. ``"created_at:desc"``. Must be in ``sortable``. */
  defaultSort: string
  /** The single key in ``defaults`` that should be debounced when written. */
  searchKey?: keyof F & string
  /** Debounce in ms for ``searchKey``. Default 300. */
  searchDebounce?: number
  /** The data fetcher. Receives the resolved query. */
  fetcher: (q: ResolvedQuery<F>) => Promise<{ data: R[], total: number }>
}

export interface UseListQueryReturn<F extends FiltersBag, R> {
  filters: Ref<F>
  page: Ref<number>
  pageSize: Ref<number>
  sort: Ref<string>
  rows: Ref<R[]>
  total: Ref<number>
  totalPages: Ref<number>
  isLoading: Ref<boolean>
  error: Ref<string | null>
  setFilter: <K extends keyof F>(key: K, value: F[K]) => void
  resetFilters: () => void
  refresh: () => Promise<void>
}

function serialize(value: FilterPrimitive): string | null {
  if (value === null || value === undefined) return null
  if (typeof value === 'boolean') return value ? '1' : null
  if (Array.isArray(value)) return value.length ? value.join(',') : null
  if (typeof value === 'number') return Number.isFinite(value) ? String(value) : null
  const s = String(value).trim()
  return s ? s : null
}

function parseInto<F extends FiltersBag>(
  defaults: F,
  query: Record<string, string | string[] | null | undefined>
): F {
  // Internally we treat the bag as a plain dict — the generic ``F`` is
  // only there to retain the page-declared filter shape for callers.
  const defaultsDict = defaults as Record<string, unknown>
  const out: Record<string, unknown> = { ...defaultsDict }
  for (const key of Object.keys(defaultsDict)) {
    const raw = query[key]
    if (raw === undefined || raw === null) continue
    const value = Array.isArray(raw) ? raw[raw.length - 1] : raw
    if (value === undefined || value === null) continue
    const def = defaultsDict[key]
    if (typeof def === 'boolean') {
      out[key] = value === '1' || value === 'true'
    } else if (Array.isArray(def)) {
      out[key] = value === '' ? [] : value.split(',').filter(Boolean)
    } else if (typeof def === 'number') {
      const n = Number(value)
      out[key] = Number.isFinite(n) ? n : def
    } else {
      out[key] = value
    }
  }
  return out as F
}

export function useListQuery<F extends FiltersBag, R>(
  cfg: ListQueryConfig<F, R>
): UseListQueryReturn<F, R> {
  const route = useRoute()
  const router = useRouter()

  const pageSizeVal = Math.max(1, Math.min(100, cfg.pageSize ?? 20))
  const searchKey = cfg.searchKey
  const debounceMs = cfg.searchDebounce ?? 300

  // ---- State -----------------------------------------------------------
  const filters = ref<F>(parseInto(cfg.defaults, route.query as Record<string, string | string[]>))
  const page = ref<number>(Number(route.query.page) > 0 ? Number(route.query.page) : 1)
  const pageSize = ref<number>(pageSizeVal)
  const sort = ref<string>(
    cfg.sortable.includes(String(route.query.sort).split(':')[0] ?? '')
      ? String(route.query.sort)
      : cfg.defaultSort
  )
  const rows = ref<R[]>([]) as Ref<R[]>
  const total = ref<number>(0)
  const isLoading = ref<boolean>(false)
  const error = ref<string | null>(null)

  const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

  // ---- URL sync --------------------------------------------------------
  function pushUrl() {
    const next: Record<string, string> = {}
    for (const [k, v] of Object.entries(filters.value)) {
      const s = serialize(v as FilterPrimitive)
      if (s !== null) next[k] = s
    }
    if (page.value > 1) next.page = String(page.value)
    if (sort.value && sort.value !== cfg.defaultSort) next.sort = sort.value

    // Diff against current query — only push if changed.
    const cur = route.query
    let changed = false
    const allKeys = new Set([...Object.keys(cur), ...Object.keys(next)])
    for (const k of allKeys) {
      const a = next[k] ?? undefined
      const b = (Array.isArray(cur[k]) ? (cur[k] as string[]).join(',') : (cur[k] as string)) ?? undefined
      if (a !== b) {
        changed = true
        break
      }
    }
    if (!changed) return
    router.replace({ query: next })
  }

  // Debounce for search field
  let debounceTimer: ReturnType<typeof setTimeout> | null = null
  function scheduleUrl() {
    if (debounceTimer) clearTimeout(debounceTimer)
    debounceTimer = setTimeout(pushUrl, debounceMs)
  }

  onBeforeUnmount(() => {
    if (debounceTimer) clearTimeout(debounceTimer)
  })

  // ---- Fetch -----------------------------------------------------------
  let fetchToken = 0
  async function refresh() {
    const token = ++fetchToken
    isLoading.value = true
    error.value = null
    try {
      const result = await cfg.fetcher({
        filters: filters.value,
        page: page.value,
        pageSize: pageSize.value,
        sort: sort.value
      })
      // Discard stale responses
      if (token !== fetchToken) return
      rows.value = result.data
      total.value = result.total
    } catch (e: unknown) {
      if (token !== fetchToken) return
      error.value = e instanceof Error ? e.message : 'Failed to load'
      rows.value = []
      total.value = 0
    } finally {
      if (token === fetchToken) isLoading.value = false
    }
  }

  // ---- Reactivity wiring ----------------------------------------------
  // Page changes do not reset filters. Filter changes reset page to 1.
  watch(
    () => JSON.stringify(filters.value),
    (next, prev) => {
      if (next === prev) return
      page.value = 1
      if (searchKey) {
        scheduleUrl()
      } else {
        pushUrl()
      }
    }
  )
  watch(page, pushUrl)
  watch(sort, () => {
    page.value = 1
    pushUrl()
  })

  // React to URL changes from outside (back/forward, link paste)
  watch(
    () => route.query,
    (q) => {
      const parsed = parseInto(cfg.defaults, q as Record<string, string | string[]>)
      const same = JSON.stringify(parsed) === JSON.stringify(filters.value)
      if (!same) filters.value = parsed
      const nextPage = Number(q.page) > 0 ? Number(q.page) : 1
      if (nextPage !== page.value) page.value = nextPage
      const nextSort = (q.sort as string) || cfg.defaultSort
      if (
        cfg.sortable.includes((nextSort.split(':')[0] ?? '') as string)
        && nextSort !== sort.value
      ) {
        sort.value = nextSort
      }
      refresh()
    },
    { deep: true }
  )

  // First load
  refresh()

  return {
    filters: filters as Ref<F>,
    page,
    pageSize,
    sort,
    rows,
    total,
    totalPages,
    isLoading,
    error,
    setFilter<K extends keyof F>(key: K, value: F[K]) {
      filters.value = { ...filters.value, [key]: value }
    },
    resetFilters() {
      filters.value = { ...cfg.defaults }
      page.value = 1
    },
    refresh
  }
}
