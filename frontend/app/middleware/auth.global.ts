export default defineNuxtRouteMiddleware(async (to) => {
  const auth = useAuth()

  // Public routes that don't require authentication
  const publicRoutes = ['/login']
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
