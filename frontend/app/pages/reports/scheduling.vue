<script setup lang="ts">
import type {
  SchedulingSummary,
  FirstVisitsSummary,
  HoursByProfessional,
  CabinetUtilization,
  DayOfWeekStats
} from '~/composables/useReports'

const { t } = useI18n()
const router = useRouter()
const {
  fetchSchedulingSummary,
  fetchFirstVisits,
  fetchHoursByProfessional,
  fetchCabinetUtilization,
  fetchByDayOfWeek,
  formatHours,
  getDayOfWeekLabel
} = useReports()

// State
const isLoading = ref(false)
const summary = ref<SchedulingSummary | null>(null)
const firstVisits = ref<FirstVisitsSummary | null>(null)
const hoursByProfessional = ref<HoursByProfessional[]>([])
const cabinetUtilization = ref<CabinetUtilization[]>([])
const dayOfWeekStats = ref<DayOfWeekStats[]>([])

// Date range
const today = new Date()
const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1)
const dateFrom = ref(firstDayOfMonth.toISOString().split('T')[0])
const dateTo = ref(today.toISOString().split('T')[0])

// Quick date range options
const dateRangeOptions = computed(() => [
  { label: t('reports.billing.thisMonth'), value: 'month' },
  { label: t('reports.billing.thisQuarter'), value: 'quarter' },
  { label: t('reports.billing.thisYear'), value: 'year' },
  { label: t('reports.billing.lastMonth'), value: 'last_month' },
  { label: t('reports.billing.lastQuarter'), value: 'last_quarter' },
  { label: t('reports.billing.lastYear'), value: 'last_year' }
])
const selectedRange = ref('month')

watch(selectedRange, (range) => {
  const now = new Date()
  let from: Date
  let to: Date

  switch (range) {
    case 'month':
      from = new Date(now.getFullYear(), now.getMonth(), 1)
      to = now
      break
    case 'quarter': {
      const quarter = Math.floor(now.getMonth() / 3)
      from = new Date(now.getFullYear(), quarter * 3, 1)
      to = now
      break
    }
    case 'year':
      from = new Date(now.getFullYear(), 0, 1)
      to = now
      break
    case 'last_month':
      from = new Date(now.getFullYear(), now.getMonth() - 1, 1)
      to = new Date(now.getFullYear(), now.getMonth(), 0)
      break
    case 'last_quarter': {
      const lastQuarter = Math.floor(now.getMonth() / 3) - 1
      const year = lastQuarter < 0 ? now.getFullYear() - 1 : now.getFullYear()
      const q = lastQuarter < 0 ? 3 : lastQuarter
      from = new Date(year, q * 3, 1)
      to = new Date(year, q * 3 + 3, 0)
      break
    }
    case 'last_year':
      from = new Date(now.getFullYear() - 1, 0, 1)
      to = new Date(now.getFullYear() - 1, 11, 31)
      break
    default:
      return
  }

  dateFrom.value = from.toISOString().split('T')[0]
  dateTo.value = to.toISOString().split('T')[0]
})

// Load all report data
async function loadReports() {
  isLoading.value = true

  try {
    const [summaryData, firstVisitsData, hoursData, cabinetData, dayOfWeekData] = await Promise.all([
      fetchSchedulingSummary(dateFrom.value, dateTo.value),
      fetchFirstVisits(dateFrom.value, dateTo.value),
      fetchHoursByProfessional(dateFrom.value, dateTo.value),
      fetchCabinetUtilization(dateFrom.value, dateTo.value),
      fetchByDayOfWeek(dateFrom.value, dateTo.value)
    ])

    summary.value = summaryData
    firstVisits.value = firstVisitsData
    hoursByProfessional.value = hoursData
    cabinetUtilization.value = cabinetData
    dayOfWeekStats.value = dayOfWeekData
  } catch (e) {
    console.error('Failed to load scheduling reports:', e)
  } finally {
    isLoading.value = false
  }
}

// Reload when dates change
watch([dateFrom, dateTo], () => {
  loadReports()
})

onMounted(() => {
  loadReports()
})

// Format percentage
function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`
}

// Get max value for bar charts
const maxDayCount = computed(() => {
  return Math.max(...dayOfWeekStats.value.map(d => d.appointment_count), 1)
})

function goBack() {
  router.push('/reports')
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-4">
        <UButton
          variant="ghost"
          color="neutral"
          icon="i-lucide-arrow-left"
          @click="goBack"
        />
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
            {{ t('reports.scheduling.title') }}
          </h1>
          <p class="text-sm text-gray-500">
            {{ t('reports.scheduling.description') }}
          </p>
        </div>
      </div>
    </div>

    <!-- Date Range Filters -->
    <UCard>
      <div class="flex flex-wrap items-end gap-4">
        <UFormField :label="t('reports.billing.period')">
          <USelectMenu
            v-model="selectedRange"
            :items="dateRangeOptions"
            value-key="value"
            class="w-48"
          />
        </UFormField>

        <UFormField :label="t('reports.billing.from')">
          <UInput
            v-model="dateFrom"
            type="date"
          />
        </UFormField>

        <UFormField :label="t('reports.billing.to')">
          <UInput
            v-model="dateTo"
            type="date"
          />
        </UFormField>

        <UButton
          :loading="isLoading"
          @click="loadReports"
        >
          {{ t('reports.billing.refresh') }}
        </UButton>
      </div>
    </UCard>

    <!-- Loading state -->
    <div
      v-if="isLoading"
      class="flex justify-center py-12"
    >
      <UIcon
        name="i-lucide-loader-2"
        class="h-8 w-8 animate-spin text-primary-500"
      />
    </div>

    <template v-else>
      <!-- Summary Cards -->
      <div
        v-if="summary"
        class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
      >
        <UCard>
          <div class="text-center">
            <p class="text-sm text-gray-500 dark:text-gray-400">
              {{ t('reports.scheduling.labels.totalAppointments') }}
            </p>
            <p class="text-2xl font-bold text-gray-900 dark:text-white">
              {{ summary.total_appointments }}
            </p>
          </div>
        </UCard>

        <UCard>
          <div class="text-center">
            <p class="text-sm text-gray-500 dark:text-gray-400">
              {{ t('reports.scheduling.labels.completionRate') }}
            </p>
            <p class="text-2xl font-bold text-green-600">
              {{ formatPercent(summary.completion_rate) }}
            </p>
            <p class="text-sm text-gray-500">
              {{ summary.completed }} {{ t('reports.scheduling.labels.completed') }}
            </p>
          </div>
        </UCard>

        <UCard>
          <div class="text-center">
            <p class="text-sm text-gray-500 dark:text-gray-400">
              {{ t('reports.scheduling.labels.cancellationRate') }}
            </p>
            <p
              class="text-2xl font-bold"
              :class="summary.cancellation_rate > 20 ? 'text-red-600' : 'text-amber-600'"
            >
              {{ formatPercent(summary.cancellation_rate) }}
            </p>
            <p class="text-sm text-gray-500">
              {{ summary.cancelled }} {{ t('reports.scheduling.labels.cancelled') }}
            </p>
          </div>
        </UCard>

        <UCard>
          <div class="text-center">
            <p class="text-sm text-gray-500 dark:text-gray-400">
              {{ t('reports.scheduling.labels.noShowRate') }}
            </p>
            <p
              class="text-2xl font-bold"
              :class="summary.no_show_rate > 10 ? 'text-red-600' : 'text-amber-600'"
            >
              {{ formatPercent(summary.no_show_rate) }}
            </p>
            <p class="text-sm text-gray-500">
              {{ summary.no_show }} {{ t('reports.scheduling.labels.noShows') }}
            </p>
          </div>
        </UCard>
      </div>

      <!-- First Visits Card -->
      <div
        v-if="firstVisits"
        class="grid grid-cols-1 md:grid-cols-3 gap-4"
      >
        <UCard>
          <div class="text-center">
            <p class="text-sm text-gray-500 dark:text-gray-400">
              {{ t('reports.scheduling.features.firstVisits') }}
            </p>
            <p class="text-2xl font-bold text-purple-600">
              {{ firstVisits.new_patients }}
            </p>
            <p class="text-sm text-gray-500">
              {{ t('reports.scheduling.labels.newPatients') }}
            </p>
          </div>
        </UCard>

        <UCard>
          <div class="text-center">
            <p class="text-sm text-gray-500 dark:text-gray-400">
              {{ t('reports.scheduling.labels.firstVisitRate') }}
            </p>
            <p class="text-2xl font-bold text-blue-600">
              {{ formatPercent(firstVisits.first_visit_rate) }}
            </p>
            <p class="text-sm text-gray-500">
              {{ t('reports.scheduling.labels.ofTotalAppointments') }}
            </p>
          </div>
        </UCard>

        <UCard>
          <div class="text-center">
            <p class="text-sm text-gray-500 dark:text-gray-400">
              {{ t('reports.scheduling.labels.appointmentsInPeriod') }}
            </p>
            <p class="text-2xl font-bold text-gray-900 dark:text-white">
              {{ firstVisits.total_appointments }}
            </p>
            <p class="text-sm text-gray-500">
              {{ t('reports.scheduling.labels.excludingCancelled') }}
            </p>
          </div>
        </UCard>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Hours by Professional -->
        <UCard>
          <template #header>
            <h3 class="font-semibold text-gray-900 dark:text-white">
              {{ t('reports.scheduling.features.hoursWorked') }}
            </h3>
          </template>

          <div
            v-if="hoursByProfessional.length > 0"
            class="space-y-4"
          >
            <div
              v-for="prof in hoursByProfessional"
              :key="prof.professional_id || 'unknown'"
              class="flex items-center justify-between"
            >
              <div class="flex items-center gap-2">
                <UAvatar
                  :alt="prof.professional_name"
                  size="sm"
                />
                <div>
                  <p class="text-gray-700 dark:text-gray-300">
                    {{ prof.professional_name }}
                  </p>
                  <p class="text-xs text-gray-500">
                    {{ prof.appointment_count }} {{ t('reports.scheduling.labels.appointments') }}
                  </p>
                </div>
              </div>
              <div class="text-right">
                <p class="font-semibold text-gray-900 dark:text-white">
                  {{ formatHours(prof.total_minutes) }}
                </p>
                <div class="flex items-center gap-2 text-xs text-gray-500">
                  <span class="text-green-600">{{ prof.completed_count }} ✓</span>
                  <span class="text-red-600">{{ prof.cancelled_count }} ✗</span>
                  <span class="text-amber-600">{{ prof.no_show_count }} ⊘</span>
                </div>
              </div>
            </div>
          </div>
          <p
            v-else
            class="text-gray-500 text-center py-4"
          >
            {{ t('reports.billing.noData') }}
          </p>
        </UCard>

        <!-- Cabinet Utilization -->
        <UCard>
          <template #header>
            <h3 class="font-semibold text-gray-900 dark:text-white">
              {{ t('reports.scheduling.features.cabinetUtilization') }}
            </h3>
          </template>

          <div
            v-if="cabinetUtilization.length > 0"
            class="space-y-4"
          >
            <div
              v-for="cabinet in cabinetUtilization"
              :key="cabinet.cabinet"
              class="flex items-center justify-between"
            >
              <div class="flex items-center gap-2">
                <UIcon
                  name="i-lucide-armchair"
                  class="h-5 w-5 text-purple-500"
                />
                <div>
                  <p class="text-gray-700 dark:text-gray-300">
                    {{ cabinet.cabinet }}
                  </p>
                  <p class="text-xs text-gray-500">
                    {{ cabinet.appointment_count }} {{ t('reports.scheduling.labels.appointments') }}
                  </p>
                </div>
              </div>
              <div class="text-right">
                <p class="font-semibold text-gray-900 dark:text-white">
                  {{ formatHours(cabinet.total_minutes) }}
                </p>
                <p class="text-xs text-gray-500">
                  {{ cabinet.completed_count }} {{ t('reports.scheduling.labels.completed') }}
                </p>
              </div>
            </div>
          </div>
          <p
            v-else
            class="text-gray-500 text-center py-4"
          >
            {{ t('reports.billing.noData') }}
          </p>
        </UCard>

        <!-- Day of Week Distribution -->
        <UCard class="lg:col-span-2">
          <template #header>
            <div class="flex items-center justify-between">
              <h3 class="font-semibold text-gray-900 dark:text-white">
                {{ t('reports.scheduling.labels.byDayOfWeek') }}
              </h3>
              <!-- Legend -->
              <div class="flex items-center gap-4 text-xs">
                <div class="flex items-center gap-1">
                  <div class="w-3 h-3 rounded bg-green-500" />
                  <span class="text-gray-600 dark:text-gray-400">{{ t('reports.scheduling.labels.completed') }}</span>
                </div>
                <div class="flex items-center gap-1">
                  <div class="w-3 h-3 rounded bg-red-500" />
                  <span class="text-gray-600 dark:text-gray-400">{{ t('reports.scheduling.labels.cancelled') }}</span>
                </div>
                <div class="flex items-center gap-1">
                  <div class="w-3 h-3 rounded bg-amber-500" />
                  <span class="text-gray-600 dark:text-gray-400">{{ t('reports.scheduling.labels.noShows') }}</span>
                </div>
              </div>
            </div>
          </template>

          <div
            v-if="dayOfWeekStats.length > 0"
            class="space-y-3"
          >
            <div
              v-for="day in dayOfWeekStats"
              :key="day.day_of_week"
              class="flex items-center gap-4"
            >
              <div class="w-24 text-sm text-gray-700 dark:text-gray-300">
                {{ getDayOfWeekLabel(day.day_name) }}
              </div>
              <div class="flex-1">
                <div class="flex items-center gap-2">
                  <!-- Stacked bar container -->
                  <div
                    class="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-4 overflow-hidden"
                  >
                    <div
                      class="flex h-4"
                      :style="{ width: `${(day.appointment_count / maxDayCount) * 100}%` }"
                    >
                      <!-- Completed (green) -->
                      <div
                        v-if="day.completed_count > 0"
                        class="bg-green-500 h-4 transition-all"
                        :style="{ width: `${(day.completed_count / day.appointment_count) * 100}%` }"
                        :title="`${day.completed_count} ${t('reports.scheduling.labels.completed')}`"
                      />
                      <!-- Cancelled (red) -->
                      <div
                        v-if="day.cancelled_count > 0"
                        class="bg-red-500 h-4 transition-all"
                        :style="{ width: `${(day.cancelled_count / day.appointment_count) * 100}%` }"
                        :title="`${day.cancelled_count} ${t('reports.scheduling.labels.cancelled')}`"
                      />
                      <!-- No-show (amber) -->
                      <div
                        v-if="day.no_show_count > 0"
                        class="bg-amber-500 h-4 transition-all"
                        :style="{ width: `${(day.no_show_count / day.appointment_count) * 100}%` }"
                        :title="`${day.no_show_count} ${t('reports.scheduling.labels.noShows')}`"
                      />
                      <!-- Other statuses (gray) -->
                      <div
                        v-if="day.appointment_count - day.completed_count - day.cancelled_count - day.no_show_count > 0"
                        class="bg-gray-400 h-4 transition-all"
                        :style="{ width: `${((day.appointment_count - day.completed_count - day.cancelled_count - day.no_show_count) / day.appointment_count) * 100}%` }"
                        :title="`${day.appointment_count - day.completed_count - day.cancelled_count - day.no_show_count} ${t('reports.scheduling.labels.pending')}`"
                      />
                    </div>
                  </div>
                  <span class="text-sm font-medium w-12 text-right text-gray-900 dark:text-white">
                    {{ day.appointment_count }}
                  </span>
                </div>
              </div>
            </div>
          </div>
          <p
            v-else
            class="text-gray-500 text-center py-4"
          >
            {{ t('reports.billing.noData') }}
          </p>
        </UCard>
      </div>

      <!-- Status Breakdown (Additional Info) -->
      <UCard v-if="summary">
        <template #header>
          <h3 class="font-semibold text-gray-900 dark:text-white">
            {{ t('reports.scheduling.labels.statusBreakdown') }}
          </h3>
        </template>

        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <div class="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <UIcon
              name="i-lucide-calendar"
              class="h-6 w-6 mx-auto text-gray-500 mb-1"
            />
            <p class="text-lg font-semibold text-gray-900 dark:text-white">
              {{ summary.scheduled }}
            </p>
            <p class="text-xs text-gray-500">
              {{ t('appointments.scheduled') }}
            </p>
          </div>

          <div class="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <UIcon
              name="i-lucide-calendar-check"
              class="h-6 w-6 mx-auto text-blue-500 mb-1"
            />
            <p class="text-lg font-semibold text-gray-900 dark:text-white">
              {{ summary.confirmed }}
            </p>
            <p class="text-xs text-gray-500">
              {{ t('appointments.confirmed') }}
            </p>
          </div>

          <div class="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <UIcon
              name="i-lucide-play-circle"
              class="h-6 w-6 mx-auto text-amber-500 mb-1"
            />
            <p class="text-lg font-semibold text-gray-900 dark:text-white">
              {{ summary.in_progress }}
            </p>
            <p class="text-xs text-gray-500">
              {{ t('appointments.inProgress') }}
            </p>
          </div>

          <div class="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <UIcon
              name="i-lucide-check-circle"
              class="h-6 w-6 mx-auto text-green-500 mb-1"
            />
            <p class="text-lg font-semibold text-gray-900 dark:text-white">
              {{ summary.completed }}
            </p>
            <p class="text-xs text-gray-500">
              {{ t('appointments.completed') }}
            </p>
          </div>

          <div class="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <UIcon
              name="i-lucide-x-circle"
              class="h-6 w-6 mx-auto text-red-500 mb-1"
            />
            <p class="text-lg font-semibold text-gray-900 dark:text-white">
              {{ summary.cancelled }}
            </p>
            <p class="text-xs text-gray-500">
              {{ t('appointments.cancelled') }}
            </p>
          </div>

          <div class="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <UIcon
              name="i-lucide-user-x"
              class="h-6 w-6 mx-auto text-orange-500 mb-1"
            />
            <p class="text-lg font-semibold text-gray-900 dark:text-white">
              {{ summary.no_show }}
            </p>
            <p class="text-xs text-gray-500">
              {{ t('appointments.noShow') }}
            </p>
          </div>
        </div>
      </UCard>
    </template>
  </div>
</template>
