import type { User, UserCreate, UserRole, UserUpdate, PaginatedResponse, ApiResponse } from '~/types'

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
    { value: 'dentist', label: 'Odontólogo' },
    { value: 'hygienist', label: 'Higienista' },
    { value: 'assistant', label: 'Auxiliar' },
    { value: 'receptionist', label: 'Recepcionista' }
  ]

  async function fetchUsers(): Promise<void> {
    isLoading.value = true
    error.value = null

    try {
      // The backend returns users with their clinic membership info in paginated format
      const response = await api.get<PaginatedResponse<ClinicUser>>('/api/v1/auth/users')
      users.value = response.data
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
      const response = await api.post<ApiResponse<User>>('/api/v1/auth/users', data as unknown as Record<string, unknown>)
      toast.add({
        title: t('common.success', 'Success'),
        description: 'Usuario creado correctamente',
        color: 'success'
      })
      // Refresh the user list
      await fetchUsers()
      return response.data
    } catch (e: unknown) {
      const fetchError = e as { statusCode?: number, data?: { message?: string, detail?: string } }
      if (fetchError.statusCode === 409) {
        error.value = 'El email ya existe'
        toast.add({
          title: t('common.error'),
          description: 'El email ya existe',
          color: 'error'
        })
      } else if (fetchError.statusCode === 422) {
        error.value = fetchError.data?.message || fetchError.data?.detail || 'Datos incorrectos'
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

  async function updateUser(userId: string, data: UserUpdate): Promise<ClinicUser | null> {
    isLoading.value = true
    error.value = null

    try {
      const response = await api.put<ApiResponse<ClinicUser>>(`/api/v1/auth/users/${userId}`, data as unknown as Record<string, unknown>)
      toast.add({
        title: t('common.success', 'Success'),
        description: 'Usuario actualizado correctamente',
        color: 'success'
      })
      // Refresh the user list
      await fetchUsers()
      return response.data
    } catch (e: unknown) {
      const fetchError = e as { statusCode?: number, data?: { message?: string, detail?: string } }
      if (fetchError.statusCode === 409) {
        error.value = 'El email ya existe'
        toast.add({
          title: t('common.error'),
          description: 'El email ya existe',
          color: 'error'
        })
      } else if (fetchError.statusCode === 400) {
        error.value = fetchError.data?.message || fetchError.data?.detail || 'Operacion no permitida'
        toast.add({
          title: t('common.error'),
          description: error.value,
          color: 'error'
        })
      } else if (fetchError.statusCode === 404) {
        error.value = 'Usuario no encontrado'
        toast.add({
          title: t('common.error'),
          description: 'Usuario no encontrado',
          color: 'error'
        })
      } else {
        error.value = 'Error al actualizar usuario'
        toast.add({
          title: t('common.error'),
          description: 'Error al actualizar usuario',
          color: 'error'
        })
      }
      console.error('Failed to update user:', e)
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function deleteUser(userId: string): Promise<boolean> {
    isLoading.value = true
    error.value = null

    try {
      await api.del(`/api/v1/auth/users/${userId}`)
      toast.add({
        title: t('common.success', 'Success'),
        description: 'Usuario eliminado de la clinica',
        color: 'success'
      })
      // Refresh the user list
      await fetchUsers()
      return true
    } catch (e: unknown) {
      const fetchError = e as { statusCode?: number, data?: { message?: string, detail?: string } }
      if (fetchError.statusCode === 400) {
        error.value = fetchError.data?.message || fetchError.data?.detail || 'Operacion no permitida'
        toast.add({
          title: t('common.error'),
          description: error.value,
          color: 'error'
        })
      } else if (fetchError.statusCode === 404) {
        error.value = 'Usuario no encontrado'
        toast.add({
          title: t('common.error'),
          description: 'Usuario no encontrado',
          color: 'error'
        })
      } else {
        error.value = 'Error al eliminar usuario'
        toast.add({
          title: t('common.error'),
          description: 'Error al eliminar usuario',
          color: 'error'
        })
      }
      console.error('Failed to delete user:', e)
      return false
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
    createUser,
    updateUser,
    deleteUser
  }
}
