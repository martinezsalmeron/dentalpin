import type { ModuleDefinition, NavigationItem } from '~/types'
import { PERMISSIONS } from '~/config/permissions'

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
  label: 'Clinical',
  icon: 'i-lucide-stethoscope',
  navigation: [
    {
      label: 'nav.dashboard',
      icon: 'i-lucide-home',
      to: '/'
      // Dashboard accessible to all authenticated users
    },
    {
      label: 'nav.patients',
      icon: 'i-lucide-users',
      to: '/patients',
      permission: PERMISSIONS.patients.read
    },
    {
      label: 'nav.appointments',
      icon: 'i-lucide-calendar',
      to: '/appointments',
      permission: PERMISSIONS.appointments.read
    }
  ]
})

// Settings module
registerModule({
  name: 'settings',
  label: 'Settings',
  icon: 'i-lucide-settings',
  navigation: [
    {
      label: 'nav.settings',
      icon: 'i-lucide-settings',
      to: '/settings'
      // Settings accessible to all authenticated users
    }
  ]
})
