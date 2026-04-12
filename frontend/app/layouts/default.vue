<script setup lang="ts">
const { t } = useI18n()
const auth = useAuth()
const clinic = useClinic()
const { navigationItems } = useModules()
const route = useRoute()

// Sidebar state
const isSidebarCollapsed = useState('sidebar:collapsed', () => false)

// Persist sidebar state
if (import.meta.client) {
  const savedState = localStorage.getItem('sidebar:collapsed')
  if (savedState !== null) {
    isSidebarCollapsed.value = savedState === 'true'
  }
}

function toggleSidebar() {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
  if (import.meta.client) {
    localStorage.setItem('sidebar:collapsed', String(isSidebarCollapsed.value))
  }
}

async function handleLogout() {
  await auth.logout()
}

// Check if nav item is active
function isActive(to: string): boolean {
  if (to === '/') {
    return route.path === '/'
  }
  // Exact match
  if (route.path === to) {
    return true
  }
  // Check if route starts with this path (potential child route)
  if (route.path.startsWith(to + '/')) {
    // But not if there's a more specific nav item that matches
    const moreSpecificNavItem = navigationItems.value.find(item =>
      item.to !== to
      && item.to.length > to.length
      && route.path.startsWith(item.to)
    )
    return !moreSpecificNavItem
  }
  return false
}
</script>

<template>
  <div class="min-h-screen flex bg-gray-50 dark:bg-gray-950">
    <!-- Sidebar -->
    <aside
      class="fixed inset-y-0 left-0 z-50 flex flex-col border-r border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 transition-all duration-200 ease-out"
      :class="isSidebarCollapsed ? 'w-16' : 'w-60'"
    >
      <!-- Logo -->
      <div class="flex items-center h-16 px-4 border-b border-gray-200 dark:border-gray-800">
        <NuxtLink
          to="/"
          class="flex items-center gap-2 overflow-hidden"
        >
          <UIcon
            name="i-lucide-smile"
            class="w-8 h-8 text-primary-500 shrink-0"
          />
          <span
            v-if="!isSidebarCollapsed"
            class="font-semibold text-lg text-gray-900 dark:text-white truncate"
          >
            DentalPin
          </span>
        </NuxtLink>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
        <NuxtLink
          v-for="item in navigationItems"
          :key="item.to"
          :to="item.to"
          class="flex items-center gap-3 px-3 py-2 rounded-lg transition-colors"
          :class="[
            isActive(item.to)
              ? 'bg-primary-50 dark:bg-primary-950 text-primary-600 dark:text-primary-400'
              : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
          ]"
        >
          <UIcon
            :name="item.icon"
            class="w-5 h-5 shrink-0"
          />
          <span
            v-if="!isSidebarCollapsed"
            class="truncate"
          >
            {{ item.label }}
          </span>
        </NuxtLink>
      </nav>

      <!-- User section -->
      <div class="border-t border-gray-200 dark:border-gray-800 p-4">
        <div
          v-if="auth.user.value"
          class="flex items-center gap-3"
        >
          <UAvatar
            :alt="auth.user.value.first_name"
            size="sm"
            class="shrink-0"
          />
          <div
            v-if="!isSidebarCollapsed"
            class="flex-1 min-w-0"
          >
            <p class="text-sm font-medium text-gray-900 dark:text-white truncate">
              {{ auth.user.value.first_name }} {{ auth.user.value.last_name }}
            </p>
            <p class="text-xs text-gray-500 dark:text-gray-400 truncate">
              {{ auth.user.value.email }}
            </p>
          </div>
        </div>
      </div>
    </aside>

    <!-- Main content -->
    <div
      class="flex-1 flex flex-col transition-all duration-200 ease-out"
      :class="isSidebarCollapsed ? 'ml-16' : 'ml-60'"
    >
      <!-- Header -->
      <header class="sticky top-0 z-40 flex items-center h-16 px-4 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
        <!-- Toggle sidebar -->
        <UButton
          variant="ghost"
          color="neutral"
          size="sm"
          :icon="isSidebarCollapsed ? 'i-lucide-panel-left-open' : 'i-lucide-panel-left-close'"
          @click="toggleSidebar"
        />

        <!-- Clinic name -->
        <div class="ml-4 flex items-center gap-2">
          <UIcon
            name="i-lucide-building-2"
            class="w-4 h-4 text-gray-500"
          />
          <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
            {{ clinic.clinicName.value || 'Clínica' }}
          </span>
        </div>

        <div class="flex-1" />

        <!-- Right side actions -->
        <div class="flex items-center gap-2">
          <UColorModeButton />

          <UButton
            variant="ghost"
            color="neutral"
            size="sm"
            icon="i-lucide-log-out"
            @click="handleLogout"
          >
            <span class="hidden sm:inline">{{ t('auth.logout') }}</span>
          </UButton>
        </div>
      </header>

      <!-- Page content -->
      <main class="flex-1 p-6">
        <slot />
      </main>
    </div>
  </div>
</template>
