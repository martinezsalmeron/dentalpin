import { getModules, getNavigationItems } from '~/utils/moduleRegistry'
import type { ModuleDefinition, NavigationItem } from '~/types'

export function useModules() {
  const { t } = useI18n()
  const { can } = usePermissions()

  const modules = computed<ModuleDefinition[]>(() => getModules())

  // Filter navigation items based on user permissions
  const navigationItems = computed<NavigationItem[]>(() => {
    return getNavigationItems()
      .filter((item) => {
        // If no permission required, show to all
        if (!item.permission) {
          return true
        }
        // Check if user has the required permission
        return can(item.permission)
      })
      .map(item => ({
        ...item,
        label: t(item.label)
      }))
  })

  return {
    modules,
    navigationItems
  }
}
