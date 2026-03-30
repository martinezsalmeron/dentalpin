import type { ApiResponse, PaginatedResponse } from '~/types'

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

interface UseApiOptions {
  method?: HttpMethod
  body?: Record<string, unknown> | null
  headers?: Record<string, string>
  skipAuth?: boolean
}

export function useApi() {
  const config = useRuntimeConfig()
  const auth = useAuth()
  const { t } = useI18n()
  const toast = useToast()

  async function $api<T>(
    path: string,
    options: UseApiOptions = {}
  ): Promise<T> {
    const { skipAuth, method, body, headers: optionHeaders } = options

    const headers: Record<string, string> = {
      ...(optionHeaders || {})
    }

    // Add auth header if authenticated and not skipping auth
    if (!skipAuth && auth.accessToken.value) {
      headers.Authorization = `Bearer ${auth.accessToken.value}`
    }

    try {
      return await $fetch<T>(path, {
        baseURL: config.public.apiBaseUrl,
        timeout: 10000, // 10 seconds
        method,
        body,
        headers
      })
    } catch (error: unknown) {
      const fetchError = error as { statusCode?: number, data?: { message?: string } }

      // Handle specific error codes
      if (fetchError.statusCode === 401) {
        // Try to refresh token
        const refreshed = await auth.refresh()
        if (refreshed) {
          // Retry the request with new token
          headers.Authorization = `Bearer ${auth.accessToken.value}`
          return await $fetch<T>(path, {
            baseURL: config.public.apiBaseUrl,
            method,
            body,
            headers
          })
        }
        // Redirect to login
        await auth.logout()
        throw error
      }

      if (fetchError.statusCode === 403) {
        toast.add({
          title: t('common.error'),
          description: t('common.forbidden', 'Acceso denegado'),
          color: 'error'
        })
        throw error
      }

      if (fetchError.statusCode === 404) {
        throw error
      }

      if (fetchError.statusCode === 409) {
        // Conflict - let the caller handle it
        throw error
      }

      if (fetchError.statusCode === 422) {
        // Validation error - let the caller handle it
        throw error
      }

      if (fetchError.statusCode && fetchError.statusCode >= 500) {
        toast.add({
          title: t('common.error'),
          description: t('common.serverError'),
          color: 'error'
        })
        throw error
      }

      // Network error
      if (!fetchError.statusCode) {
        toast.add({
          title: t('common.error'),
          description: t('common.networkError'),
          color: 'error'
        })
      }

      throw error
    }
  }

  // Convenience methods
  async function get<T>(path: string, options: Omit<UseApiOptions, 'method' | 'body'> = {}): Promise<T> {
    return $api<T>(path, { ...options, method: 'GET' })
  }

  async function post<T>(path: string, body?: Record<string, unknown> | null, options: Omit<UseApiOptions, 'method' | 'body'> = {}): Promise<T> {
    return $api<T>(path, { ...options, method: 'POST', body })
  }

  async function put<T>(path: string, body?: Record<string, unknown> | null, options: Omit<UseApiOptions, 'method' | 'body'> = {}): Promise<T> {
    return $api<T>(path, { ...options, method: 'PUT', body })
  }

  async function patch<T>(path: string, body?: Record<string, unknown> | null, options: Omit<UseApiOptions, 'method' | 'body'> = {}): Promise<T> {
    return $api<T>(path, { ...options, method: 'PATCH', body })
  }

  async function del<T>(path: string, options: Omit<UseApiOptions, 'method' | 'body'> = {}): Promise<T> {
    return $api<T>(path, { ...options, method: 'DELETE' })
  }

  return {
    $api,
    get,
    post,
    put,
    patch,
    del
  }
}

// Type helpers for API responses
export type { ApiResponse, PaginatedResponse }
