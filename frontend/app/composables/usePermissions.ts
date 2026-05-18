import { PERMISSIONS } from '~/config/permissions'

export function usePermissions() {
  const auth = useAuth()
  const permissions = computed<string[]>(() => auth.permissions.value ?? [])

  function can(permission: string): boolean {
    return permissions.value.includes(permission)
  }

  function canAny(perms: string[]): boolean {
    return perms.some(p => permissions.value.includes(p))
  }

  function canAll(perms: string[]): boolean {
    return perms.every(p => permissions.value.includes(p))
  }

  const isAdmin = computed(() => can(PERMISSIONS.users.write))

  return {
    permissions: readonly(permissions),
    can,
    canAny,
    canAll,
    isAdmin
  }
}
