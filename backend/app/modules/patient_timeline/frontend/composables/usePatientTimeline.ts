import type { ApiResponse, TimelineCategory, TimelineEntry, TimelineResponse } from '~~/app/types'

export function usePatientTimeline(patientId: Ref<string | undefined>) {
  const api = useApi()
  const { t } = useI18n()

  const entries = ref<TimelineEntry[]>([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const hasMore = ref(false)
  const selectedCategory = ref<TimelineCategory | null>(null)

  const isLoading = ref(false)
  const isLoadingMore = ref(false)
  const error = ref<string | null>(null)

  async function fetchTimeline(reset = true) {
    if (!patientId.value) return

    if (reset) {
      isLoading.value = true
      page.value = 1
      entries.value = []
    } else {
      isLoadingMore.value = true
    }

    error.value = null

    try {
      const params = new URLSearchParams({
        page: page.value.toString(),
        page_size: pageSize.value.toString()
      })

      if (selectedCategory.value) {
        params.append('category', selectedCategory.value)
      }

      const response = await api.get<ApiResponse<TimelineResponse>>(
        `/api/v1/patient_timeline/patients/${patientId.value}?${params.toString()}`
      )

      if (reset) {
        entries.value = response.data.entries
      } else {
        entries.value = [...entries.value, ...response.data.entries]
      }

      total.value = response.data.total
      hasMore.value = response.data.has_more
    } catch (e) {
      error.value = 'Failed to fetch timeline'
      console.error('Failed to fetch patient timeline:', e)
    } finally {
      isLoading.value = false
      isLoadingMore.value = false
    }
  }

  async function loadMore() {
    if (!hasMore.value || isLoadingMore.value) return
    page.value++
    await fetchTimeline(false)
  }

  function setCategory(category: TimelineCategory | null) {
    selectedCategory.value = category
    fetchTimeline(true)
  }

  // Get icon for event type
  function getEventIcon(eventType: string): string {
    const icons: Record<string, string> = {
      'appointment.scheduled': 'i-lucide-calendar',
      'appointment.completed': 'i-lucide-calendar-check',
      'appointment.cancelled': 'i-lucide-calendar-x',
      'appointment.no_show': 'i-lucide-calendar-off',
      'odontogram.treatment.performed': 'i-lucide-stethoscope',
      'treatment_plan.created': 'i-lucide-clipboard-list',
      'treatment_plan.treatment_completed': 'i-lucide-clipboard-check',
      'budget.sent': 'i-lucide-send',
      'budget.accepted': 'i-lucide-file-check',
      'invoice.issued': 'i-lucide-receipt',
      'invoice.paid': 'i-lucide-banknote',
      'email.sent': 'i-lucide-mail',
      'email.failed': 'i-lucide-mail-warning',
      'patient.medical_updated': 'i-lucide-heart-pulse',
      'document.uploaded': 'i-lucide-file-plus'
    }
    return icons[eventType] || 'i-lucide-circle-dot'
  }

  // Get color for category
  function getCategoryColor(category: TimelineCategory): string {
    const colors: Record<string, string> = {
      visit: 'primary',
      treatment: 'success',
      financial: 'warning',
      communication: 'info',
      medical: 'error',
      document: 'neutral'
    }
    return colors[category] || 'neutral'
  }

  // Category filter options
  const categoryOptions = computed(() => [
    { label: t('patients.timeline.categories.all'), value: null },
    { label: t('patients.timeline.categories.visit'), value: 'visit' as TimelineCategory },
    { label: t('patients.timeline.categories.treatment'), value: 'treatment' as TimelineCategory },
    { label: t('patients.timeline.categories.financial'), value: 'financial' as TimelineCategory },
    { label: t('patients.timeline.categories.communication'), value: 'communication' as TimelineCategory },
    { label: t('patients.timeline.categories.medical'), value: 'medical' as TimelineCategory },
    { label: t('patients.timeline.categories.document'), value: 'document' as TimelineCategory }
  ])

  // Watch patientId and fetch when it changes
  watch(patientId, (newId) => {
    if (newId) {
      fetchTimeline(true)
    } else {
      entries.value = []
      total.value = 0
      hasMore.value = false
    }
  }, { immediate: true })

  return {
    entries,
    total,
    page,
    pageSize,
    hasMore,
    selectedCategory,
    isLoading,
    isLoadingMore,
    error,
    categoryOptions,
    // Methods
    fetchTimeline,
    loadMore,
    setCategory,
    getEventIcon,
    getCategoryColor
  }
}
