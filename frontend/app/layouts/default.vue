<script setup lang="ts">
const { t } = useI18n()
const auth = useAuth()
const clinic = useClinic()
const { navigationItems, ensureLoaded } = useModules()
const { init: initDensity } = useDensity()
const route = useRoute()

// Pull the backend-driven nav on mount + on every route change, so
// sidebar reflects module installs/upgrades without a full reload.
// ensureLoaded enforces a 60s freshness window internally.
ensureLoaded()

watch(
  () => auth.accessToken.value,
  (token) => {
    if (token) ensureLoaded(true)
  }
)

watch(
  () => route.path,
  () => {
    ensureLoaded()
  }
)

// Sidebar state
const isSidebarCollapsed = useState('sidebar:collapsed', () => false)

// Persist sidebar + init density on client
onMounted(() => {
  const savedState = localStorage.getItem('sidebar:collapsed')
  if (savedState !== null) {
    isSidebarCollapsed.value = savedState === 'true'
  }
  initDensity()
})

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
  if (route.path === to) {
    return true
  }
  if (route.path.startsWith(to + '/')) {
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
  <div class="min-h-screen flex bg-canvas">
    <!-- Sidebar: warm muted surface, no right border (separation by colour) -->
    <aside
      class="fixed inset-y-0 left-0 z-50 flex flex-col bg-surface-muted transition-[width] duration-150 ease-out"
      :class="isSidebarCollapsed ? 'w-16' : 'w-60'"
    >
      <!-- Logo -->
      <div class="flex items-center h-14 px-4">
        <NuxtLink
          to="/"
          class="flex items-center gap-2 overflow-hidden"
          aria-label="DentalPin"
        >
          <img
            src="/logo-icon.svg"
            alt=""
            width="32"
            height="32"
            class="shrink-0"
          >
          <span
            v-if="!isSidebarCollapsed"
            class="text-h2 text-default truncate"
          >
            DentalPin
          </span>
        </NuxtLink>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 px-2 py-2 space-y-1 overflow-y-auto">
        <NuxtLink
          v-for="item in navigationItems"
          :key="item.to"
          :to="item.to"
          class="group flex items-center gap-3 px-3 py-2 rounded-token-md text-ui transition-colors"
          :class="[
            isActive(item.to)
              ? 'bg-[var(--color-primary-soft)] text-[var(--color-primary-soft-text)]'
              : 'text-muted hover:bg-surface hover:text-default'
          ]"
        >
          <UIcon
            :name="item.icon"
            class="w-[18px] h-[18px] shrink-0"
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
      <div class="px-3 py-3 border-t border-subtle">
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
            <p class="text-ui text-default truncate">
              {{ auth.user.value.first_name }} {{ auth.user.value.last_name }}
            </p>
            <p class="text-caption text-subtle truncate">
              {{ auth.user.value.email }}
            </p>
          </div>
        </div>
      </div>
    </aside>

    <!-- Main column -->
    <div
      class="flex-1 flex flex-col transition-[margin] duration-150 ease-out"
      :class="isSidebarCollapsed ? 'ml-16' : 'ml-60'"
    >
      <!-- Header -->
      <header class="sticky top-0 z-40 flex items-center h-14 px-4 bg-surface border-b border-subtle">
        <UButton
          variant="ghost"
          color="neutral"
          size="sm"
          :icon="isSidebarCollapsed ? 'i-lucide-panel-left-open' : 'i-lucide-panel-left-close'"
          :aria-label="t('nav.toggleSidebar', 'Alternar barra lateral')"
          @click="toggleSidebar"
        />

        <!-- Clinic name -->
        <div class="ml-4 flex items-center gap-2">
          <UIcon
            name="i-lucide-building-2"
            class="w-4 h-4 text-subtle"
          />
          <span class="text-ui text-muted">
            {{ clinic.clinicName.value || 'Clínica' }}
          </span>
        </div>

        <div class="flex-1" />

        <!-- Right actions -->
        <div class="flex items-center gap-1">
          <DensityToggle />
          <UColorModeButton />
          <UButton
            variant="ghost"
            color="neutral"
            size="sm"
            icon="i-lucide-log-out"
            :aria-label="t('auth.logout')"
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
