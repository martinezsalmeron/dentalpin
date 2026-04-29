/**
 * Centralized permission configuration.
 *
 * All permission checks should reference this config instead of
 * hardcoding permission strings throughout the codebase.
 */

// Resource-action permission mapping
export const PERMISSIONS = {
  patients: {
    read: 'patients.read',
    write: 'patients.write'
  },
  medicalHistory: {
    read: 'patients_clinical.medical.read',
    write: 'patients_clinical.medical.write'
  },
  emergencyContact: {
    read: 'patients_clinical.emergency.read',
    write: 'patients_clinical.emergency.write'
  },
  appointments: {
    read: 'agenda.appointments.read',
    write: 'agenda.appointments.write'
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
    admin: 'budget.admin',
    renegotiate: 'budget.renegotiate',
    acceptInClinic: 'budget.accept_in_clinic'
  },
  billing: {
    read: 'billing.read',
    write: 'billing.write',
    admin: 'billing.admin'
  },
  notifications: {
    templatesRead: 'notifications.templates.read',
    templatesWrite: 'notifications.templates.write',
    preferencesRead: 'notifications.preferences.read',
    preferencesWrite: 'notifications.preferences.write',
    logsRead: 'notifications.logs.read',
    send: 'notifications.send',
    settingsRead: 'notifications.settings.read',
    settingsWrite: 'notifications.settings.write'
  },
  reports: {
    billingRead: 'reports.billing.read',
    budgetsRead: 'reports.budgets.read',
    schedulingRead: 'reports.scheduling.read'
  },
  documents: {
    read: 'media.documents.read',
    write: 'media.documents.write'
  },
  treatmentPlans: {
    read: 'treatment_plan.plans.read',
    write: 'treatment_plan.plans.write',
    confirm: 'treatment_plan.plans.confirm',
    close: 'treatment_plan.plans.close',
    reactivate: 'treatment_plan.plans.reactivate'
  },
  clinicalNotes: {
    read: 'clinical_notes.notes.read',
    write: 'clinical_notes.notes.write'
  },
  agents: {
    view: 'agents.view',
    supervise: 'agents.supervise',
    configure: 'agents.configure',
    manage: 'agents.manage'
  },
  admin: {
    clinicRead: 'admin.clinic.read',
    clinicWrite: 'admin.clinic.write'
  }
} as const

// Route permission mapping (path -> required permission)
export const ROUTE_PERMISSIONS: Record<string, string> = {
  '/patients': PERMISSIONS.patients.read,
  '/appointments': PERMISSIONS.appointments.read,
  '/settings/users': PERMISSIONS.users.write,
  '/settings/modules': PERMISSIONS.admin.clinicRead,
  '/settings/notifications': PERMISSIONS.notifications.settingsRead,
  '/treatment-plans': PERMISSIONS.treatmentPlans.read,
  '/treatment-plans/pipeline': PERMISSIONS.treatmentPlans.read,
  '/budgets': PERMISSIONS.budget.read,
  '/settings/budgets': PERMISSIONS.admin.clinicRead,
  '/invoices': PERMISSIONS.billing.read,
  '/reports': PERMISSIONS.reports.billingRead,
  '/reports/billing': PERMISSIONS.reports.billingRead,
  '/reports/budgets': PERMISSIONS.reports.budgetsRead,
  '/reports/scheduling': PERMISSIONS.reports.schedulingRead
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
