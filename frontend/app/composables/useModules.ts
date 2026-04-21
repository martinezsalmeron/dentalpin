/**
 * Backend-driven module + navigation registry.
 *
 * Fetches ``GET /api/v1/modules/-/active`` once per session and caches
 * the result in :func:`useState`. The sidebar consumes
 * ``navigationItems`` — entries are permission-filtered on the server
 * and re-translated client-side via i18n. ``ensureLoaded`` is
 * idempotent so guards / layouts can call it without coordinating.
 *
 * If the fetch fails (offline, auth missing, network hiccup) the
 * static :mod:`utils/moduleRegistry` is used as a fallback so the UI
 * never shows a blank sidebar for authenticated users.
 */

import type { ActiveModule, ApiResponse, NavigationItem } from '~/types'
import {
  HOST_NAV,
  getModules as getStaticModules,
  getNavigationItems as getStaticNav
} from '~/utils/moduleRegistry'

export function useModules() {
  const { t } = useI18n()
  const { can } = usePermissions()
  const auth = useAuth()
  const api = useApi()

  const active = useState<ActiveModule[] | null>('modules:active', () => null)
  const loading = useState<boolean>('modules:active:loading', () => false)
  const error = useState<string | null>('modules:active:error', () => null)
  const lastLoadedAt = useState<number>('modules:active:at', () => 0)

  async function ensureLoaded(force = false): Promise<void> {
    if (!auth.accessToken.value) return
    if (loading.value) return

    const age = Date.now() - lastLoadedAt.value
    const FRESH_MS = 60_000 // 1 min — cheap enough to refetch often
    if (!force && active.value !== null && age < FRESH_MS) return

    loading.value = true
    error.value = null
    try {
      const response = await api.get<ApiResponse<ActiveModule[]>>(
        '/api/v1/modules/-/active'
      )
      active.value = response.data
      lastLoadedAt.value = Date.now()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load modules'
      console.warn('useModules: falling back to static registry —', error.value)
      active.value = null // keep the cached fallback transparent
    } finally {
      loading.value = false
    }
  }

  // All modules — either from backend response or the static fallback.
  const modules = computed(() => {
    if (active.value) {
      return active.value.map(m => ({
        name: m.name,
        label: m.name,
        icon: '',
        navigation: m.navigation
      }))
    }
    return getStaticModules()
  })

  const navigationItems = computed<NavigationItem[]>(() => {
    const moduleNav = active.value
      ? active.value.flatMap(m => m.navigation)
      : getStaticNav()

    // Host-owned entries (dashboard + settings) aren't published by any
    // module; merge them on top of the backend-driven list.
    const raw = active.value ? [...HOST_NAV, ...moduleNav] : moduleNav

    return raw
      .filter(item => !item.permission || can(item.permission))
      .slice()
      .sort((a, b) => (a.order ?? 999) - (b.order ?? 999))
      .map(item => ({ ...item, label: t(item.label) }))
  })

  return {
    modules,
    navigationItems,
    active,
    loading,
    error,
    ensureLoaded
  }
}
