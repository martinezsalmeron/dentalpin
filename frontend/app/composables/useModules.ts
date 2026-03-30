import { getModules, getNavigationItems } from '~/utils/moduleRegistry'
import type { ModuleDefinition, NavigationItem } from '~/types'

export function useModules() {
  const { t } = useI18n()

  const modules = computed<ModuleDefinition[]>(() => getModules())

  const navigationItems = computed<NavigationItem[]>(() => {
    return getNavigationItems().map(item => ({
      ...item,
      label: t(item.label)
    }))
  })

  return {
    modules,
    navigationItems
  }
}
