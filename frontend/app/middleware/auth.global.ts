export default defineNuxtRouteMiddleware(async (to) => {
  const auth = useAuth()

  // Public routes that don't require authentication.
  // ``/p/budget/<token>`` is the patient-facing budget view (ADR 0006).
  // Server-side authorization happens via the public-link 2FA cookie
  // scoped to the token; the global auth middleware must let the page
  // render so the SPA can run the /meta + /verify dance.
  const publicRoutes = ['/login', '/p/budget']
  const isPublicRoute = publicRoutes.some(route => to.path === route || to.path.startsWith(route + '/'))

  // Initialize auth state (fetch user if token exists) - works on both server and client
  await auth.init()

  if (!auth.isAuthenticated.value && !isPublicRoute) {
    // Redirect to login
    return navigateTo('/login')
  }

  if (auth.isAuthenticated.value && to.path === '/login') {
    // Already authenticated, redirect to home
    return navigateTo('/')
  }
})
