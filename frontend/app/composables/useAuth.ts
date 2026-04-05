import type { User, LoginCredentials, AuthResponse, MeResponse } from '~/types'

export function useAuth() {
  const config = useRuntimeConfig()
  const router = useRouter()

  // State
  const user = useState<User | null>('auth:user', () => null)
  const permissions = useState<string[]>('auth:permissions', () => [])
  const accessToken = useCookie('access_token', {
    maxAge: 60 * 15, // 15 minutes
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
      baseURL: config.public.apiBaseUrl,
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
        baseURL: config.public.apiBaseUrl,
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
      const response = await $fetch<MeResponse>('/api/v1/auth/me', {
        baseURL: config.public.apiBaseUrl,
        headers: {
          Authorization: `Bearer ${accessToken.value}`
        }
      })
      user.value = response.user
      permissions.value = response.permissions
    } catch {
      // Token might be expired, try to refresh
      const refreshed = await refresh()
      if (!refreshed) {
        await logout()
      }
    }
  }

  // Initialize user on client side if token exists
  async function init(): Promise<void> {
    if (import.meta.client && accessToken.value && !user.value) {
      await fetchUser()
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
