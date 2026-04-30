/**
 * Route-level permission gates.
 *
 * Permission strings match the backend manifest format exactly
 * (`<module>.<resource>.<action>`). The backend is the single source
 * of truth — see each module's `manifest.role_permissions`.
 */

// Route permission mapping (path -> required permission)
export const ROUTE_PERMISSIONS: Record<string, string> = {
  '/patients': 'patients.read',
  '/appointments': 'agenda.appointments.read',
  '/settings/users': 'admin.users.write',
  '/settings/modules': 'admin.clinic.read',
  '/settings/notifications': 'notifications.settings.read',
  '/treatment-plans': 'treatment_plan.plans.read',
  '/budgets': 'budget.read',
  '/settings/budgets': 'admin.clinic.read',
  '/invoices': 'billing.read',
  '/reports': 'reports.billing.read',
  '/reports/billing': 'reports.billing.read',
  '/reports/budgets': 'reports.budgets.read',
  '/reports/scheduling': 'reports.scheduling.read'
}

// Helper to check if a route requires permission
export function getRoutePermission(path: string): string | undefined {
  // Check exact match first
  if (ROUTE_PERMISSIONS[path]) {
    return ROUTE_PERMISSIONS[path]
  }
  // Check prefix match for nested routes
  for (const [route, permission] of Object.entries(ROUTE_PERMISSIONS)) {
    if (path.startsWith(route + '/')) {
      return permission
    }
  }
  return undefined
}
