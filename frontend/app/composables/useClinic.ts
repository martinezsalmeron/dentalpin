import type { Cabinet, CabinetCreate, CabinetUpdate, Clinic, ClinicMembership, ClinicUpdate, PaginatedResponse, ApiResponse } from '~/types'

export function useClinic() {
  const api = useApi()
  const auth = useAuth()
  const toast = useToast()
  const { t } = useI18n()

  // State
  const currentClinic = useState<Clinic | null>('clinic:current', () => null)
  const membership = useState<ClinicMembership | null>('clinic:membership', () => null)
  const isLoading = useState<boolean>('clinic:loading', () => false)

  // Computed
  const clinicName = computed(() => currentClinic.value?.name || '')
  const cabinets = computed(() => currentClinic.value?.cabinets || [])
  const slotDuration = computed(() => currentClinic.value?.settings?.slot_duration_min || 15)

  // Actions
  async function fetchClinic(): Promise<void> {
    if (!auth.isAuthenticated.value) {
      return
    }

    isLoading.value = true
    try {
      // Get user's clinics (for MVP, we just use the first one)
      const response = await api.get<PaginatedResponse<Clinic>>('/api/v1/clinical/clinics')
      if (response.data.length > 0) {
        currentClinic.value = response.data[0] ?? null
      }
    } catch (error) {
      console.error('Failed to fetch clinic:', error)
    } finally {
      isLoading.value = false
    }
  }

  async function updateClinic(data: ClinicUpdate): Promise<Clinic | null> {
    try {
      const response = await api.put<ApiResponse<Clinic>>('/api/v1/clinical/clinics', data as unknown as Record<string, unknown>)
      toast.add({
        title: t('common.success', 'Success'),
        description: 'Clinica actualizada correctamente',
        color: 'success'
      })
      await fetchClinic()
      return response.data
    } catch (e: unknown) {
      toast.add({
        title: t('common.error'),
        description: 'Error al actualizar la clinica',
        color: 'error'
      })
      console.error('Failed to update clinic:', e)
      return null
    }
  }

  async function createCabinet(data: CabinetCreate): Promise<Cabinet | null> {
    try {
      const response = await api.post<ApiResponse<Cabinet>>('/api/v1/agenda/cabinets', data as unknown as Record<string, unknown>)
      toast.add({
        title: t('common.success', 'Success'),
        description: 'Gabinete creado correctamente',
        color: 'success'
      })
      await fetchClinic()
      return response.data
    } catch (e: unknown) {
      const fetchError = e as { statusCode?: number }
      if (fetchError.statusCode === 409) {
        toast.add({
          title: t('common.error'),
          description: 'Ya existe un gabinete con ese nombre',
          color: 'error'
        })
      } else {
        toast.add({
          title: t('common.error'),
          description: 'Error al crear gabinete',
          color: 'error'
        })
      }
      console.error('Failed to create cabinet:', e)
      return null
    }
  }

  async function updateCabinet(cabinetId: string, data: CabinetUpdate): Promise<Cabinet | null> {
    try {
      const response = await api.put<ApiResponse<Cabinet>>(`/api/v1/agenda/cabinets/${cabinetId}`, data as unknown as Record<string, unknown>)
      toast.add({
        title: t('common.success', 'Success'),
        description: 'Gabinete actualizado correctamente',
        color: 'success'
      })
      await fetchClinic()
      return response.data
    } catch (e: unknown) {
      const fetchError = e as { statusCode?: number }
      if (fetchError.statusCode === 409) {
        toast.add({
          title: t('common.error'),
          description: 'Ya existe un gabinete con ese nombre',
          color: 'error'
        })
      } else if (fetchError.statusCode === 404) {
        toast.add({
          title: t('common.error'),
          description: 'Gabinete no encontrado',
          color: 'error'
        })
      } else {
        toast.add({
          title: t('common.error'),
          description: 'Error al actualizar gabinete',
          color: 'error'
        })
      }
      console.error('Failed to update cabinet:', e)
      return null
    }
  }

  async function deleteCabinet(cabinetId: string): Promise<boolean> {
    try {
      await api.del(`/api/v1/agenda/cabinets/${cabinetId}`)
      toast.add({
        title: t('common.success', 'Success'),
        description: 'Gabinete eliminado correctamente',
        color: 'success'
      })
      await fetchClinic()
      return true
    } catch (e: unknown) {
      const fetchError = e as { statusCode?: number }
      if (fetchError.statusCode === 404) {
        toast.add({
          title: t('common.error'),
          description: 'Gabinete no encontrado',
          color: 'error'
        })
      } else {
        toast.add({
          title: t('common.error'),
          description: 'Error al eliminar gabinete',
          color: 'error'
        })
      }
      console.error('Failed to delete cabinet:', e)
      return false
    }
  }

  // Initialize clinic when auth state changes
  watch(() => auth.isAuthenticated.value, async (isAuth) => {
    if (isAuth && !currentClinic.value) {
      await fetchClinic()
    } else if (!isAuth) {
      currentClinic.value = null
      membership.value = null
    }
  }, { immediate: true })

  return {
    currentClinic: readonly(currentClinic),
    membership: readonly(membership),
    isLoading: readonly(isLoading),
    clinicName,
    cabinets,
    slotDuration,
    fetchClinic,
    updateClinic,
    createCabinet,
    updateCabinet,
    deleteCabinet
  }
}
