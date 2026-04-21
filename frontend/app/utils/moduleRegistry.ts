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

// --- Host shell nav -----------------------------------------------------
//
// Dashboard + Settings belong to the host app (per Fase B Q8). They stay
// static because they don't live in any module, and they are merged with
// the backend-driven module nav in `useModules`.

export const HOST_NAV: NavigationItem[] = [
  {
    label: 'nav.dashboard',
    icon: 'i-lucide-home',
    to: '/',
    order: 0
  },
  {
    label: 'nav.settings',
    icon: 'i-lucide-settings',
    to: '/settings',
    order: 900
  }
]

// --- Static fallback (used only when /modules/-/active fails) -----------

registerModule({
  name: 'host',
  label: 'Host',
  icon: 'i-lucide-home',
  navigation: HOST_NAV
})

registerModule({
  name: 'clinical',
  label: 'Clinical',
  icon: 'i-lucide-stethoscope',
  navigation: [
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
    },
    {
      label: 'nav.treatmentPlans',
      icon: 'i-lucide-clipboard-list',
      to: '/treatment-plans',
      permission: PERMISSIONS.treatmentPlans.read
    },
    {
      label: 'nav.budgets',
      icon: 'i-lucide-file-text',
      to: '/budgets',
      permission: PERMISSIONS.budget.read
    },
    {
      label: 'nav.invoices',
      icon: 'i-lucide-receipt',
      to: '/invoices',
      permission: PERMISSIONS.billing.read
    },
    {
      label: 'nav.reports',
      icon: 'i-lucide-bar-chart-3',
      to: '/reports',
      permission: PERMISSIONS.reports.billingRead
    }
  ]
})
