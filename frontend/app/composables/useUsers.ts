import type { User, UserCreate, UserRole } from '~/types'

export interface ClinicUser {
  id: string
  email: string
  first_name: string
  last_name: string
  is_active: boolean
  role: UserRole
  created_at: string
}

export function useUsers() {
  const api = useApi()
  const toast = useToast()
  const { t } = useI18n()

  const users = ref<ClinicUser[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Available roles for user creation
  const availableRoles: { value: UserRole, label: string }[] = [
    { value: 'admin', label: 'Administrador' },
    { value: 'dentist', label: 'Dentista' },
    { value: 'hygienist', label: 'Higienista' },
    { value: 'assistant', label: 'Auxiliar' },
    { value: 'receptionist', label: 'Recepcionista' }
  ]

  async function fetchUsers(): Promise<void> {
    isLoading.value = true
    error.value = null

    try {
      // The backend returns users with their clinic membership info
      const response = await api.get<ClinicUser[]>('/api/v1/auth/users')
      users.value = response
    } catch (e) {
      error.value = 'Error al cargar usuarios'
      console.error('Failed to fetch users:', e)
    } finally {
      isLoading.value = false
    }
  }

  async function createUser(data: UserCreate): Promise<User | null> {
    isLoading.value = true
    error.value = null

    try {
      const response = await api.post<User>('/api/v1/auth/users', data as unknown as Record<string, unknown>)
      toast.add({
        title: t('common.success', 'Success'),
        description: 'Usuario creado correctamente',
        color: 'success'
      })
      // Refresh the user list
      await fetchUsers()
      return response
    } catch (e: unknown) {
      const fetchError = e as { statusCode?: number, data?: { detail?: string } }
      if (fetchError.statusCode === 409) {
        error.value = 'El email ya existe'
        toast.add({
          title: t('common.error'),
          description: 'El email ya existe',
          color: 'error'
        })
      } else if (fetchError.statusCode === 422) {
        error.value = fetchError.data?.detail || 'Datos incorrectos'
        toast.add({
          title: t('common.error'),
          description: error.value,
          color: 'error'
        })
      } else {
        error.value = 'Error al crear usuario'
        toast.add({
          title: t('common.error'),
          description: 'Error al crear usuario',
          color: 'error'
        })
      }
      console.error('Failed to create user:', e)
      return null
    } finally {
      isLoading.value = false
    }
  }

  return {
    users: readonly(users),
    isLoading: readonly(isLoading),
    error: readonly(error),
    availableRoles,
    fetchUsers,
    createUser
  }
}
