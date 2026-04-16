<script setup lang="ts">
interface Props {
  patientId: string
}

const props = defineProps<Props>()

const { t } = useI18n()

const patientIdRef = computed(() => props.patientId)

const {
  entries,
  total,
  hasMore,
  selectedCategory,
  isLoading,
  isLoadingMore,
  categoryOptions,
  loadMore,
  setCategory,
  getEventIcon,
  getCategoryColor
} = usePatientTimeline(patientIdRef)

// Format date for display
function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24))

  if (diffDays === 0) {
    return t('common.today') + ' ' + date.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })
  } else if (diffDays === 1) {
    return t('common.yesterday') + ' ' + date.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })
  } else if (diffDays < 7) {
    return date.toLocaleDateString('es-ES', { weekday: 'long', hour: '2-digit', minute: '2-digit' })
  } else {
    return date.toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
  }
}

// Intersection observer for infinite scroll
const loadMoreTrigger = ref<HTMLElement | null>(null)

onMounted(() => {
  if (!loadMoreTrigger.value) return

  const observer = new IntersectionObserver(
    (entries) => {
      if (entries[0].isIntersecting && hasMore.value && !isLoadingMore.value) {
        loadMore()
      }
    },
    { threshold: 0.1 }
  )

  observer.observe(loadMoreTrigger.value)

  onUnmounted(() => {
    observer.disconnect()
  })
})
</script>

<template>
  <div class="patient-timeline">
    <!-- Category Filter -->
    <div class="flex flex-wrap gap-2 mb-4">
      <UButton
        v-for="option in categoryOptions"
        :key="option.value || 'all'"
        :variant="selectedCategory === option.value ? 'solid' : 'outline'"
        size="sm"
        @click="setCategory(option.value)"
      >
        {{ option.label }}
      </UButton>
    </div>

    <!-- Loading State -->
    <div
      v-if="isLoading"
      class="space-y-4"
    >
      <USkeleton
        v-for="i in 5"
        :key="i"
        class="h-20 w-full"
      />
    </div>

    <!-- Empty State -->
    <div
      v-else-if="entries.length === 0"
      class="text-center py-12 text-gray-500"
    >
      <UIcon
        name="i-lucide-clock"
        class="w-12 h-12 mx-auto mb-4 opacity-50"
      />
      <p>{{ t('patients.timeline.empty') }}</p>
    </div>

    <!-- Timeline Entries -->
    <div
      v-else
      class="relative"
    >
      <!-- Timeline line -->
      <div class="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200 dark:bg-gray-700" />

      <div class="space-y-4">
        <div
          v-for="entry in entries"
          :key="entry.id"
          class="relative pl-10"
        >
          <!-- Timeline dot -->
          <div
            class="absolute left-2 w-5 h-5 rounded-full flex items-center justify-center"
            :class="`bg-${getCategoryColor(entry.event_category)}-100 dark:bg-${getCategoryColor(entry.event_category)}-900`"
          >
            <UIcon
              :name="getEventIcon(entry.event_type)"
              class="w-3 h-3"
              :class="`text-${getCategoryColor(entry.event_category)}-600 dark:text-${getCategoryColor(entry.event_category)}-400`"
            />
          </div>

          <!-- Entry Card -->
          <UCard
            class="ml-2"
            :ui="{ body: { padding: 'p-3' } }"
          >
            <div class="flex items-start justify-between">
              <div>
                <h4 class="font-medium">
                  {{ entry.title }}
                </h4>
                <p
                  v-if="entry.description"
                  class="text-sm text-gray-500 mt-1"
                >
                  {{ entry.description }}
                </p>
              </div>
              <UBadge
                :color="getCategoryColor(entry.event_category)"
                variant="subtle"
                size="xs"
              >
                {{ entry.event_category }}
              </UBadge>
            </div>
            <div class="mt-2 text-xs text-gray-400">
              {{ formatDate(entry.occurred_at) }}
            </div>
          </UCard>
        </div>

        <!-- Load More Trigger -->
        <div
          ref="loadMoreTrigger"
          class="h-4"
        />

        <!-- Loading More Indicator -->
        <div
          v-if="isLoadingMore"
          class="flex justify-center py-4"
        >
          <UIcon
            name="i-lucide-loader-2"
            class="w-6 h-6 animate-spin text-gray-400"
          />
        </div>

        <!-- End of Timeline -->
        <div
          v-else-if="!hasMore && entries.length > 0"
          class="text-center py-4 text-sm text-gray-400"
        >
          {{ t('patients.timeline.endOfTimeline') }}
        </div>
      </div>
    </div>

    <!-- Total Count -->
    <div
      v-if="total > 0"
      class="mt-4 text-sm text-gray-500 text-center"
    >
      {{ t('patients.timeline.totalEntries', { count: total }) }}
    </div>
  </div>
</template>

<style scoped>
.patient-timeline {
  width: 100%;
}
</style>
