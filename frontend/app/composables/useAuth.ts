import type { User, LoginCredentials, AuthResponse, MeResponse, ApiResponse } from '~/types'

export function useAuth() {
  const config = useRuntimeConfig()
  const router = useRouter()

  // Use different API URL for server (Docker internal) vs client (browser)
  const apiBaseUrl = computed(() =>
    import.meta.server ? config.apiBaseUrlServer : config.public.apiBaseUrl
  )

  // State
  const user = useState<User | null>('auth:user', () => null)
  const permissions = useState<string[]>('auth:permissions', () => [])
  // Cookie lifetime matches refresh token; JWT expiry is enforced by the
  // backend, and a 401 triggers refresh in useApi. Matching the access
  // cookie's maxAge to the 15min JWT TTL caused premature logouts.
  const accessToken = useCookie('access_token', {
    maxAge: 60 * 60 * 24 * 7, // 7 days
    secure: import.meta.env.PROD,
    sameSite: 'lax'
  })
  const refreshToken = useCookie('refresh_token', {
    maxAge: 60 * 60 * 24 * 7, // 7 days
    secure: import.meta.env.PROD,
    sameSite: 'lax'
  })

  // Computed
  const isAuthenticated = computed(() => !!accessToken.value && !!user.value)

  // Actions
  async function login(credentials: LoginCredentials): Promise<void> {
    // OAuth2PasswordRequestForm expects form data with 'username' field
    const formData = new URLSearchParams()
    formData.append('username', credentials.email)
    formData.append('password', credentials.password)

    const response = await $fetch<AuthResponse>('/api/v1/auth/login', {
      baseURL: apiBaseUrl.value,
      method: 'POST',
      body: formData,
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    })

    accessToken.value = response.access_token
    refreshToken.value = response.refresh_token

    // Fetch user info after login
    await fetchUser()
  }

  async function logout(): Promise<void> {
    accessToken.value = null
    refreshToken.value = null
    user.value = null
    permissions.value = []
    await router.push('/login')
  }

  async function refresh(): Promise<boolean> {
    if (!refreshToken.value) {
      return false
    }

    try {
      const response = await $fetch<AuthResponse>('/api/v1/auth/refresh', {
        baseURL: apiBaseUrl.value,
        method: 'POST',
        body: { refresh_token: refreshToken.value }
      })

      accessToken.value = response.access_token
      refreshToken.value = response.refresh_token
      user.value = response.user
      return true
    } catch {
      await logout()
      return false
    }
  }

  async function fetchUser(): Promise<void> {
    if (!accessToken.value) {
      return
    }

    try {
      const response = await $fetch<ApiResponse<MeResponse>>('/api/v1/auth/me', {
        baseURL: apiBaseUrl.value,
        headers: {
          Authorization: `Bearer ${accessToken.value}`
        }
      })
      user.value = response.data.user
      permissions.value = response.data.permissions
    } catch (error: unknown) {
      const fetchError = error as { statusCode?: number }
      // Only try refresh on 401 (expired token), not on other errors
      if (fetchError.statusCode === 401) {
        const refreshed = await refresh()
        if (!refreshed) {
          await logout()
        }
      } else {
        // Log the error but don't logout on non-401 errors
        console.error('Failed to fetch user:', error)
        throw error
      }
    }
  }

  // Initialize user if token exists (works on both server and client)
  async function init(): Promise<void> {
    if (accessToken.value && !user.value) {
      await fetchUser()
    } else if (!accessToken.value && refreshToken.value) {
      // Access cookie gone but refresh still valid — recover session.
      await refresh()
    }
  }

  return {
    user: readonly(user),
    permissions: readonly(permissions),
    accessToken: readonly(accessToken),
    isAuthenticated,
    login,
    logout,
    refresh,
    fetchUser,
    init
  }
}
