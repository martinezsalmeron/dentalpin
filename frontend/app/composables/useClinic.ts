import type { Clinic, ClinicMembership } from '~/types'

export function useClinic() {
  const api = useApi()
  const auth = useAuth()

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
      const response = await api.get<{ data: Clinic[] }>('/api/v1/clinical/clinics/')
      if (response.data.length > 0) {
        currentClinic.value = response.data[0] ?? null
      }
    } catch (error) {
      console.error('Failed to fetch clinic:', error)
    } finally {
      isLoading.value = false
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
    fetchClinic
  }
}
