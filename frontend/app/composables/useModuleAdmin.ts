/**
 * Admin-only composable for the module lifecycle API.
 *
 * Distinct from `useModules` (backend-driven nav for the sidebar). This
 * one powers the /settings/modules page: install / uninstall / upgrade /
 * restart, plus status and doctor polling.
 */

import type {
  ApiResponse,
  ModuleDoctorReport,
  ModuleInfo,
  ModuleOperationLogEntry,
  ModuleOperationResult,
  ModuleStatus
} from '~/types'

const MODULES_BASE = '/api/v1/modules'

export function useModuleAdmin() {
  const api = useApi()

  const modules = ref<ModuleInfo[]>([])
  const status = ref<ModuleStatus | null>(null)
  const doctor = ref<ModuleDoctorReport | null>(null)
  const loading = ref(false)
  const applying = ref(false)
  const error = ref<string | null>(null)

  async function refresh(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const [listResp, statusResp, doctorResp] = await Promise.all([
        api.get<ApiResponse<ModuleInfo[]>>(MODULES_BASE),
        api.get<ApiResponse<ModuleStatus>>(`${MODULES_BASE}/-/status`),
        api.get<ApiResponse<ModuleDoctorReport>>(`${MODULES_BASE}/-/doctor`)
      ])
      modules.value = listResp.data
      status.value = statusResp.data
      doctor.value = doctorResp.data
    } catch (err: unknown) {
      error.value = extractMessage(err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function install(name: string, force = false): Promise<string[]> {
    const qs = force ? '?force=true' : ''
    const response = await api.post<ApiResponse<ModuleOperationResult>>(
      `${MODULES_BASE}/${encodeURIComponent(name)}/install${qs}`
    )
    await refresh()
    return response.data.scheduled
  }

  async function uninstall(name: string, force = false): Promise<void> {
    const qs = force ? '?force=true' : ''
    await api.post<ApiResponse<ModuleOperationResult>>(
      `${MODULES_BASE}/${encodeURIComponent(name)}/uninstall${qs}`
    )
    await refresh()
  }

  async function upgrade(name: string): Promise<string[]> {
    const response = await api.post<ApiResponse<ModuleOperationResult>>(
      `${MODULES_BASE}/${encodeURIComponent(name)}/upgrade`
    )
    await refresh()
    return response.data.scheduled
  }

  async function restart(): Promise<void> {
    applying.value = true
    try {
      await api.post<ApiResponse<{ pid: number }>>(`${MODULES_BASE}/-/restart`)
    } catch (err: unknown) {
      applying.value = false
      throw err
    }
  }

  /**
   * Poll /-/status every 2s until `pending=[]` or timeout. Resolves with
   * the final ModuleStatus. Throws on timeout.
   */
  async function pollUntilSettled(timeoutMs = 60_000): Promise<ModuleStatus> {
    const started = Date.now()
    let lastError: unknown = null
    // Initial grace period so SIGTERM has time to happen.
    await sleep(1_500)

    while (Date.now() - started < timeoutMs) {
      try {
        const resp = await api.get<ApiResponse<ModuleStatus>>(`${MODULES_BASE}/-/status`)
        lastError = null
        if (resp.data.pending.length === 0) {
          status.value = resp.data
          applying.value = false
          return resp.data
        }
      } catch (err) {
        // 502/503 while the backend restarts is expected; keep polling.
        lastError = err
      }
      await sleep(2_000)
    }

    applying.value = false
    if (lastError) {
      throw lastError
    }
    throw new Error('restart-timeout')
  }

  async function operations(name: string, limit = 20): Promise<ModuleOperationLogEntry[]> {
    const resp = await api.get<ApiResponse<ModuleOperationLogEntry[]>>(
      `${MODULES_BASE}/${encodeURIComponent(name)}/-/operations?limit=${limit}`
    )
    return resp.data
  }

  return {
    modules,
    status,
    doctor,
    loading,
    applying,
    error,
    refresh,
    install,
    uninstall,
    upgrade,
    restart,
    pollUntilSettled,
    operations
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

function extractMessage(err: unknown): string {
  const e = err as { data?: { detail?: string, message?: string }, message?: string }
  return e?.data?.detail || e?.data?.message || e?.message || 'unknown error'
}
