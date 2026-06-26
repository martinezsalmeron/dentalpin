import type { ApiResponse } from '~~/app/types'

export interface KapsoSettings {
  phone_number_id: string | null
  business_account_id: string | null
  display_phone_number: string | null
  has_api_key: boolean
  has_webhook_secret: boolean
  is_active: boolean
  is_verified: boolean
  last_verified_at: string | null
  last_template_sync_at: string | null
}

export interface KapsoTemplate {
  name: string
  language: string
  status: string
  category: string | null
  synced_at: string | null
}

const BASE = '/api/v1/whatsapp_kapso'

export function useKapso() {
  const api = useApi()
  const settings = useState<KapsoSettings | null>('kapso:settings', () => null)
  const templates = useState<KapsoTemplate[]>('kapso:templates', () => [])
  const loading = ref(false)
  const saving = ref(false)
  const syncing = ref(false)

  async function fetchSettings() {
    loading.value = true
    try {
      const res = await api.get<ApiResponse<KapsoSettings>>(`${BASE}/settings`)
      settings.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function saveSettings(payload: Record<string, unknown>) {
    saving.value = true
    try {
      const res = await api.put<ApiResponse<KapsoSettings>>(`${BASE}/settings`, payload)
      settings.value = res.data
      return true
    } finally {
      saving.value = false
    }
  }

  async function syncTemplates() {
    syncing.value = true
    try {
      const res = await api.post<ApiResponse<KapsoTemplate[]>>(`${BASE}/templates/sync`, {})
      templates.value = res.data
      return res.data
    } finally {
      syncing.value = false
    }
  }

  async function mapTemplate(notificationType: string, locale: string, templateName: string) {
    await api.post(`${BASE}/templates/map`, {
      notification_type: notificationType,
      locale,
      template_name: templateName
    })
  }

  async function testConnection(toNumber: string, templateName: string, language = 'es') {
    const res = await api.post<ApiResponse<{ success: boolean, error: string | null }>>(
      `${BASE}/test`,
      { to_number: toNumber, template_name: templateName, language }
    )
    return res.data
  }

  return {
    settings,
    templates,
    loading,
    saving,
    syncing,
    fetchSettings,
    saveSettings,
    syncTemplates,
    mapTemplate,
    testConnection
  }
}
