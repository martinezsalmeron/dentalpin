/**
 * Composable for checking user permissions.
 *
 * Permissions are loaded from /me endpoint and stored in useAuth.
 * Use this composable to check permissions and conditionally render UI.
 */
export function usePermissions() {
  const auth = useAuth()

  // Permissions from auth state
  const permissions = computed<string[]>(() => auth.permissions.value ?? [])

  /**
   * Check if user has a specific permission
   */
  function can(permission: string): boolean {
    return permissions.value.includes(permission)
  }

  /**
   * Check if user has any of the specified permissions
   */
  function canAny(perms: string[]): boolean {
    return perms.some(p => permissions.value.includes(p))
  }

  /**
   * Check if user has all of the specified permissions
   */
  function canAll(perms: string[]): boolean {
    return perms.every(p => permissions.value.includes(p))
  }

  // Convenience computed properties for common checks
  const canReadPatients = computed(() => can('patients.read'))
  const canWritePatients = computed(() => can('patients.write'))
  const canReadAppointments = computed(() => can('agenda.appointments.read'))
  const canWriteAppointments = computed(() => can('agenda.appointments.write'))
  const canManageUsers = computed(() => can('admin.users.write'))
  const isAdmin = computed(() => canManageUsers.value)

  return {
    permissions: readonly(permissions),
    can,
    canAny,
    canAll,
    canReadPatients,
    canWritePatients,
    canReadAppointments,
    canWriteAppointments,
    canManageUsers,
    isAdmin
  }
}
