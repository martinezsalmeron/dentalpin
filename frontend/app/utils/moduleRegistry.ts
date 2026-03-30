import type { ModuleDefinition, NavigationItem } from '~/types'

const modules: ModuleDefinition[] = []

export function registerModule(mod: ModuleDefinition): void {
  // Avoid duplicate registration
  if (modules.some(m => m.name === mod.name)) {
    return
  }
  modules.push(mod)
}

export function getModules(): ModuleDefinition[] {
  return [...modules]
}

export function getNavigationItems(): NavigationItem[] {
  return modules.flatMap(mod => mod.navigation)
}

// Register the clinical module
registerModule({
  name: 'clinical',
  label: 'Clínico',
  icon: 'i-lucide-stethoscope',
  navigation: [
    {
      label: 'nav.dashboard',
      icon: 'i-lucide-home',
      to: '/'
    },
    {
      label: 'nav.patients',
      icon: 'i-lucide-users',
      to: '/patients'
    },
    {
      label: 'nav.appointments',
      icon: 'i-lucide-calendar',
      to: '/appointments'
    }
  ]
})

// Settings is always available
registerModule({
  name: 'settings',
  label: 'Configuración',
  icon: 'i-lucide-settings',
  navigation: [
    {
      label: 'nav.settings',
      icon: 'i-lucide-settings',
      to: '/settings'
    }
  ]
})
