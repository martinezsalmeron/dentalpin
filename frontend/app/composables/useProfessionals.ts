import type { Professional, PaginatedResponse } from '~/types'

// Predefined color palette for professionals
const PROFESSIONAL_COLORS = [
  '#3B82F6', // blue
  '#10B981', // emerald
  '#8B5CF6', // violet
  '#F59E0B', // amber
  '#EF4444', // red
  '#EC4899', // pink
  '#06B6D4', // cyan
  '#84CC16' // lime
]

export function useProfessionals() {
  const api = useApi()

  const professionals = ref<Professional[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Map professional ID to assigned color
  const professionalColors = ref<Map<string, string>>(new Map())

  async function fetchProfessionals(): Promise<void> {
    isLoading.value = true
    error.value = null

    try {
      const response = await api.get<PaginatedResponse<Professional>>('/api/v1/auth/professionals')
      professionals.value = response.data

      // Assign colors to professionals
      professionalColors.value = new Map()
      response.data.forEach((prof, index) => {
        const color = PROFESSIONAL_COLORS[index % PROFESSIONAL_COLORS.length]
        if (color) {
          professionalColors.value.set(prof.id, color)
        }
      })
    } catch (e) {
      error.value = 'Error al cargar profesionales'
      console.error('Failed to fetch professionals:', e)
    } finally {
      isLoading.value = false
    }
  }

  function getProfessionalById(id: string): Professional | undefined {
    return professionals.value.find(p => p.id === id)
  }

  function getProfessionalColor(id: string): string {
    return professionalColors.value.get(id) || '#6B7280' // Default gray
  }

  function getProfessionalInitials(professional: Professional): string {
    const first = professional.first_name.charAt(0).toUpperCase()
    const last = professional.last_name.charAt(0).toUpperCase()
    return `${first}${last}`
  }

  function getProfessionalFullName(professional: Professional): string {
    return `${professional.first_name} ${professional.last_name}`
  }

  return {
    professionals: readonly(professionals),
    isLoading: readonly(isLoading),
    error: readonly(error),
    fetchProfessionals,
    getProfessionalById,
    getProfessionalColor,
    getProfessionalInitials,
    getProfessionalFullName
  }
}
