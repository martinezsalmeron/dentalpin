/**
 * Centralized permission configuration.
 *
 * All permission checks should reference this config instead of
 * hardcoding permission strings throughout the codebase.
 */

// Resource-action permission mapping
export const PERMISSIONS = {
  patients: {
    read: 'clinical.patients.read',
    write: 'clinical.patients.write'
  },
  appointments: {
    read: 'clinical.appointments.read',
    write: 'clinical.appointments.write'
  },
  users: {
    read: 'admin.users.read',
    write: 'admin.users.write'
  },
  odontogram: {
    read: 'odontogram.read',
    write: 'odontogram.write',
    treatmentsRead: 'odontogram.treatments.read',
    treatmentsWrite: 'odontogram.treatments.write'
  },
  catalog: {
    read: 'catalog.read',
    write: 'catalog.write',
    admin: 'catalog.admin'
  },
  budget: {
    read: 'budget.read',
    write: 'budget.write',
    admin: 'budget.admin'
  }
} as const

// Route permission mapping (path -> required permission)
export const ROUTE_PERMISSIONS: Record<string, string> = {
  '/patients': PERMISSIONS.patients.read,
  '/appointments': PERMISSIONS.appointments.read,
  '/settings/users': PERMISSIONS.users.write,
  '/budgets': PERMISSIONS.budget.read
}

// Helper to get permission for a resource action
export function getPermission(resource: keyof typeof PERMISSIONS, action: 'read' | 'write'): string {
  return PERMISSIONS[resource]?.[action] ?? ''
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
