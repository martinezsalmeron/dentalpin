/**
 * Settings registry — categories, pages, search index, onboarding rules.
 *
 * The settings screen is split into a small set of stable categories
 * (general, workspace, people, clinical, billing, communications,
 * integrations, modules, account). Modules contribute *pages* (full
 * child routes, mounted at ``/settings/<category>/<path>``) by calling
 * :func:`registerSettingsPage` from a Nuxt plugin — same registration
 * shape the existing slot system uses.
 *
 * State lives in :func:`useState` so SSR + HMR keep registrations
 * stable across reloads and every consumer (across layers) sees the
 * same map.
 */

import type { Component } from 'vue'

export type SettingsCategoryId
  = | 'general'
    | 'workspace'
    | 'people'
    | 'clinical'
    | 'billing'
    | 'communications'
    | 'integrations'
    | 'modules'
    | 'account'

export interface SettingsCategory {
  id: SettingsCategoryId
  labelKey: string
  descriptionKey: string
  icon: string
  order: number
  /**
   * If set, the category is hidden when the user lacks this permission
   * AND has no visible page inside it. Pages can still gate themselves
   * independently. Account has no gate (always visible).
   */
  permission?: string
}

/**
 * A registered settings page. Renders as a card on the category
 * landing and is mounted at ``/settings/<category>/<path>`` via the
 * shared dynamic route.
 *
 * If ``to`` is provided the entry behaves as an external link card
 * instead of a registered page (no component is mounted) — used for
 * pre-existing pages we don't want to move (e.g. ``/settings/modules``).
 */
export interface SettingsPageEntry {
  /** URL slug. Must be unique within its category. */
  path: string
  category: SettingsCategoryId
  labelKey: string
  descriptionKey?: string
  icon: string
  /**
   * Permission gate. A string requires that exact permission; an array
   * acts as ``canAny`` (visible if the user holds at least one). When
   * unset, the page is visible to all authenticated roles.
   */
  permission?: string | string[]
  /** Component mounted at ``/settings/<category>/<path>``. */
  component?: () => Promise<Component | { default: Component }>
  /** External link target — overrides ``component`` when set. */
  to?: string
  /** Synonyms surfaced by Cmd-K (lowercase substrings). */
  searchKeywords?: string[]
  /** Lower numbers render first. Ties resolve in registration order. */
  order?: number
  /** Renders an amber dot when truthy at resolve time. */
  attention?: () => boolean
}

export interface VisibleCategory extends SettingsCategory {
  pages: SettingsPageEntry[]
  hasAttention: boolean
}

export interface SearchEntry {
  id: string
  category: SettingsCategoryId
  label: string
  description?: string
  keywords: string[]
  to: string
  icon: string
}

export interface GettingStartedRule {
  id: string
  labelKey: string
  descriptionKey?: string
  icon?: string
  to: string
  when: () => boolean
  severity?: 'info' | 'warning' | 'critical'
}

export interface GettingStartedItem extends GettingStartedRule {
  resolved: boolean
}

const DEFAULT_CATEGORIES: readonly SettingsCategory[] = [
  {
    id: 'general',
    labelKey: 'settings.categories.general.label',
    descriptionKey: 'settings.categories.general.description',
    icon: 'i-lucide-building-2',
    order: 10
  },
  {
    id: 'workspace',
    labelKey: 'settings.categories.workspace.label',
    descriptionKey: 'settings.categories.workspace.description',
    icon: 'i-lucide-layout-grid',
    order: 20
  },
  {
    id: 'people',
    labelKey: 'settings.categories.people.label',
    descriptionKey: 'settings.categories.people.description',
    icon: 'i-lucide-users',
    order: 30,
    permission: 'admin.users.read'
  },
  {
    id: 'clinical',
    labelKey: 'settings.categories.clinical.label',
    descriptionKey: 'settings.categories.clinical.description',
    icon: 'i-lucide-stethoscope',
    order: 40
  },
  {
    id: 'billing',
    labelKey: 'settings.categories.billing.label',
    descriptionKey: 'settings.categories.billing.description',
    icon: 'i-lucide-receipt',
    order: 50
  },
  {
    id: 'communications',
    labelKey: 'settings.categories.communications.label',
    descriptionKey: 'settings.categories.communications.description',
    icon: 'i-lucide-mail',
    order: 60
  },
  {
    id: 'integrations',
    labelKey: 'settings.categories.integrations.label',
    descriptionKey: 'settings.categories.integrations.description',
    icon: 'i-lucide-plug',
    order: 70
  },
  {
    id: 'modules',
    labelKey: 'settings.categories.modules.label',
    descriptionKey: 'settings.categories.modules.description',
    icon: 'i-lucide-blocks',
    order: 80,
    permission: 'admin.clinic.read'
  },
  {
    id: 'account',
    labelKey: 'settings.categories.account.label',
    descriptionKey: 'settings.categories.account.description',
    icon: 'i-lucide-user-circle',
    order: 90
  }
]

// Module-level (NOT in `useState`) because entries carry async-component
// functions that the SSR payload cannot serialize. The plugin runs on
// both server and client, so both sides build the same registry
// independently — no transfer needed.
const _pages: SettingsPageEntry[] = []
const _rules: GettingStartedRule[] = []
// Reactive trigger so consumers re-render when registrations change
// (HMR, lazy module installs). Bumping `version` invalidates computeds.
function useRegistryVersion() {
  return useState<number>('settings:registry-version', () => 0)
}

function useDismissedState() {
  return useState<Record<string, boolean>>('settings:onboarding-dismissed', () => ({}))
}

const STORAGE_KEY_PREFIX = 'dentalpin.settings.onboarding.dismissed:'

function bumpVersion(): void {
  // Only bump on client — on server `useState` is per-request, so calling
  // it inside a plugin-time register is fine; on client the bump triggers
  // re-render after HMR.
  try {
    const v = useRegistryVersion()
    v.value = v.value + 1
  } catch {
    // useState may throw if called outside a Nuxt context (e.g. tests);
    // module-level state still works for non-reactive lookups.
  }
}

export function registerSettingsPage(entry: SettingsPageEntry): void {
  const id = `${entry.category}.${entry.path}`
  const idx = _pages.findIndex(p => `${p.category}.${p.path}` === id)
  if (idx >= 0) _pages.splice(idx, 1, entry)
  else _pages.push(entry)
  bumpVersion()
}

export function unregisterSettingsPage(category: SettingsCategoryId, path: string): void {
  const idx = _pages.findIndex(p => p.category === category && p.path === path)
  if (idx >= 0) _pages.splice(idx, 1)
  bumpVersion()
}

export function registerGettingStartedRule(rule: GettingStartedRule): void {
  const idx = _rules.findIndex(r => r.id === rule.id)
  if (idx >= 0) _rules.splice(idx, 1, rule)
  else _rules.push(rule)
  bumpVersion()
}

export function unregisterGettingStartedRule(id: string): void {
  const idx = _rules.findIndex(r => r.id === id)
  if (idx >= 0) _rules.splice(idx, 1)
  bumpVersion()
}

export function useSettingsRegistry() {
  const { t } = useI18n()
  const { can, canAny } = usePermissions()
  const auth = useAuth()

  const version = useRegistryVersion()
  const dismissed = useDismissedState()

  function isPageVisible(page: SettingsPageEntry): boolean {
    if (!page.permission) return true
    return Array.isArray(page.permission)
      ? canAny(page.permission)
      : can(page.permission)
  }

  function pagesByCategory(id: SettingsCategoryId): SettingsPageEntry[] {
    // touch `version` so this is reactive to register/unregister calls
    void version.value
    return [..._pages]
      .filter(p => p.category === id && isPageVisible(p))
      .sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
  }

  const categories = computed<VisibleCategory[]>(() => {
    return DEFAULT_CATEGORIES
      .filter(cat => !cat.permission || can(cat.permission))
      .map((cat) => {
        const visiblePages = pagesByCategory(cat.id)
        return {
          ...cat,
          pages: visiblePages,
          hasAttention: visiblePages.some(p => p.attention?.() === true)
        }
      })
      .sort((a, b) => a.order - b.order)
  })

  function findPage(categoryId: SettingsCategoryId, path: string): SettingsPageEntry | null {
    void version.value
    const entry = _pages.find(p => p.category === categoryId && p.path === path)
    return entry && isPageVisible(entry) ? entry : null
  }

  function findCategory(id: string): VisibleCategory | null {
    return categories.value.find(c => c.id === id) ?? null
  }

  function firstVisibleCategory(): VisibleCategory | null {
    return categories.value[0] ?? null
  }

  // ---- Search index ----------------------------------------------------

  const searchIndex = computed<SearchEntry[]>(() => {
    const out: SearchEntry[] = []
    for (const cat of categories.value) {
      // Category landing as a search hit.
      out.push({
        id: cat.id,
        category: cat.id,
        label: t(cat.labelKey),
        description: t(cat.descriptionKey),
        keywords: [cat.id, t(cat.labelKey).toLowerCase()],
        to: `/settings/${cat.id}`,
        icon: cat.icon
      })
      for (const page of cat.pages) {
        const label = t(page.labelKey)
        const description = page.descriptionKey ? t(page.descriptionKey) : undefined
        out.push({
          id: `${cat.id}.${page.path}`,
          category: cat.id,
          label,
          description,
          keywords: [
            page.path,
            label.toLowerCase(),
            ...(page.searchKeywords ?? []).map(k => k.toLowerCase())
          ],
          to: page.to ?? `/settings/${cat.id}/${page.path}`,
          icon: page.icon
        })
      }
    }
    return out
  })

  function search(query: string): SearchEntry[] {
    const q = query.trim().toLowerCase()
    if (!q) return searchIndex.value.slice(0, 8)
    return searchIndex.value
      .map((entry) => {
        const labelHit = entry.label.toLowerCase().includes(q)
        const keywordHit = entry.keywords.some(k => k.includes(q))
        const descHit = entry.description?.toLowerCase().includes(q) ?? false
        if (!labelHit && !keywordHit && !descHit) return null
        // Rank: label > keyword > description
        const rank = labelHit ? 0 : keywordHit ? 1 : 2
        return { entry, rank }
      })
      .filter((x): x is { entry: SearchEntry, rank: number } => x !== null)
      .sort((a, b) => a.rank - b.rank)
      .map(x => x.entry)
      .slice(0, 12)
  }

  // ---- Onboarding ------------------------------------------------------

  const clinic = useClinic()

  function dismissalKey(): string {
    const clinicId = clinic.currentClinic.value?.id ?? auth.user.value?.id ?? 'unknown'
    return `${STORAGE_KEY_PREFIX}${clinicId}`
  }

  function loadDismissed(): boolean {
    if (!import.meta.client) return false
    const key = dismissalKey()
    const raw = localStorage.getItem(key)
    return raw === '1'
  }

  function saveDismissed(value: boolean): void {
    if (!import.meta.client) return
    const key = dismissalKey()
    if (value) localStorage.setItem(key, '1')
    else localStorage.removeItem(key)
    dismissed.value = { ...dismissed.value, [key]: value }
  }

  const gettingStarted = computed<GettingStartedItem[]>(() => {
    void version.value
    return _rules
      .map(rule => ({ ...rule, resolved: !rule.when() }))
      .filter(item => !item.resolved)
  })

  const isOnboardingDismissed = computed(() => {
    const key = dismissalKey()
    if (key in dismissed.value) return dismissed.value[key]
    return loadDismissed()
  })

  function dismissOnboarding(): void {
    saveDismissed(true)
  }

  function resetOnboarding(): void {
    saveDismissed(false)
  }

  return {
    categories,
    pagesByCategory,
    findPage,
    findCategory,
    firstVisibleCategory,
    isPageVisible,
    searchIndex,
    search,
    gettingStarted,
    isOnboardingDismissed,
    dismissOnboarding,
    resetOnboarding,
    register: registerSettingsPage,
    unregister: unregisterSettingsPage,
    registerGettingStartedRule,
    unregisterGettingStartedRule
  }
}
