<script setup lang="ts">
import type {
  AppointmentFunnel,
  CabinetUtilization,
  DayOfWeekStats,
  DurationVarianceStats,
  FirstVisitsSummary,
  HoursByProfessional,
  PunctualityStats,
  SchedulingSummary,
  WaitingTimeStats
} from '~/composables/useReports'

const { t } = useI18n()
const router = useRouter()
const {
  fetchSchedulingSummary,
  fetchFirstVisits,
  fetchHoursByProfessional,
  fetchCabinetUtilization,
  fetchByDayOfWeek,
  fetchWaitingTimes,
  fetchPunctuality,
  fetchDurationVariance,
  fetchFunnel,
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
const waitingStats = ref<WaitingTimeStats | null>(null)
const punctuality = ref<PunctualityStats | null>(null)
const durationVariance = ref<DurationVarianceStats | null>(null)
const funnel = ref<AppointmentFunnel | null>(null)

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
    const [
      summaryData,
      firstVisitsData,
      hoursData,
      cabinetData,
      dayOfWeekData,
      waitData,
      punctualityData,
      durationData,
      funnelData
    ] = await Promise.all([
      fetchSchedulingSummary(dateFrom.value, dateTo.value),
      fetchFirstVisits(dateFrom.value, dateTo.value),
      fetchHoursByProfessional(dateFrom.value, dateTo.value),
      fetchCabinetUtilization(dateFrom.value, dateTo.value),
      fetchByDayOfWeek(dateFrom.value, dateTo.value),
      fetchWaitingTimes(dateFrom.value, dateTo.value),
      fetchPunctuality(dateFrom.value, dateTo.value),
      fetchDurationVariance(dateFrom.value, dateTo.value),
      fetchFunnel(dateFrom.value, dateTo.value)
    ])

    summary.value = summaryData
    firstVisits.value = firstVisitsData
    hoursByProfessional.value = hoursData
    cabinetUtilization.value = cabinetData
    dayOfWeekStats.value = dayOfWeekData
    waitingStats.value = waitData
    punctuality.value = punctualityData
    durationVariance.value = durationData
    funnel.value = funnelData
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
function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  return `${value.toFixed(1)}%`
}

function formatMinutes(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  const rounded = Math.round(value * 10) / 10
  return `${rounded} min`
}

function formatSignedMinutes(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  const sign = value > 0 ? '+' : ''
  return `${sign}${Math.round(value * 10) / 10} min`
}

// Get max value for bar charts
const maxDayCount = computed(() => {
  return Math.max(...dayOfWeekStats.value.map(d => d.appointment_count), 1)
})

const maxWaitBucket = computed(() => {
  if (!waitingStats.value) return 1
  return Math.max(...waitingStats.value.distribution.map(b => b.count), 1)
})

const maxPunctualityBucket = computed(() => {
  if (!punctuality.value) return 1
  return Math.max(...punctuality.value.distribution.map(b => b.count), 1)
})

const funnelStageLabels: Record<string, string> = {
  scheduled: 'appointments.status.scheduled',
  confirmed: 'appointments.status.confirmed',
  checked_in: 'appointments.status.checked_in',
  in_treatment: 'appointments.status.in_treatment',
  completed: 'appointments.status.completed',
  cancelled: 'appointments.status.cancelled',
  no_show: 'appointments.status.no_show'
}

const funnelRows = computed(() => {
  if (!funnel.value) return []
  const order: Array<keyof typeof funnelStageLabels> = [
    'scheduled',
    'confirmed',
    'checked_in',
    'in_treatment',
    'completed',
    'cancelled',
    'no_show'
  ]
  const max = Math.max(...Object.values(funnel.value.counts_by_status), 1)
  return order.map((stage) => ({
    stage,
    labelKey: funnelStageLabels[stage],
    count: funnel.value!.counts_by_status[stage] ?? 0,
    widthPct: ((funnel.value!.counts_by_status[stage] ?? 0) / max) * 100
  }))
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
          <h1 class="text-display text-default">
            {{ t('reports.scheduling.title') }}
          </h1>
          <p class="text-caption text-subtle">
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
        class="h-8 w-8 animate-spin text-primary-accent"
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
            <p class="text-caption text-subtle">
              {{ t('reports.scheduling.labels.totalAppointments') }}
            </p>
            <p class="text-display text-default">
              {{ summary.total_appointments }}
            </p>
          </div>
        </UCard>

        <UCard>
          <div class="text-center">
            <p class="text-caption text-subtle">
              {{ t('reports.scheduling.labels.completionRate') }}
            </p>
            <p class="text-display text-default text-success-accent">
              {{ formatPercent(summary.completion_rate) }}
            </p>
            <p class="text-caption text-subtle">
              {{ summary.completed }} {{ t('reports.scheduling.labels.completed') }}
            </p>
          </div>
        </UCard>

        <UCard>
          <div class="text-center">
            <p class="text-caption text-subtle">
              {{ t('reports.scheduling.labels.cancellationRate') }}
            </p>
            <p
              class="text-display text-default"
              :class="summary.cancellation_rate > 20 ? 'text-danger-accent' : 'text-warning-accent'"
            >
              {{ formatPercent(summary.cancellation_rate) }}
            </p>
            <p class="text-caption text-subtle">
              {{ summary.cancelled }} {{ t('reports.scheduling.labels.cancelled') }}
            </p>
          </div>
        </UCard>

        <UCard>
          <div class="text-center">
            <p class="text-caption text-subtle">
              {{ t('reports.scheduling.labels.noShowRate') }}
            </p>
            <p
              class="text-display text-default"
              :class="summary.no_show_rate > 10 ? 'text-danger-accent' : 'text-warning-accent'"
            >
              {{ formatPercent(summary.no_show_rate) }}
            </p>
            <p class="text-caption text-subtle">
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
            <p class="text-caption text-subtle">
              {{ t('reports.scheduling.features.firstVisits') }}
            </p>
            <p class="text-display text-default text-purple-600">
              {{ firstVisits.new_patients }}
            </p>
            <p class="text-caption text-subtle">
              {{ t('reports.scheduling.labels.newPatients') }}
            </p>
          </div>
        </UCard>

        <UCard>
          <div class="text-center">
            <p class="text-caption text-subtle">
              {{ t('reports.scheduling.labels.firstVisitRate') }}
            </p>
            <p class="text-display text-default text-info-accent">
              {{ formatPercent(firstVisits.first_visit_rate) }}
            </p>
            <p class="text-caption text-subtle">
              {{ t('reports.scheduling.labels.ofTotalAppointments') }}
            </p>
          </div>
        </UCard>

        <UCard>
          <div class="text-center">
            <p class="text-caption text-subtle">
              {{ t('reports.scheduling.labels.appointmentsInPeriod') }}
            </p>
            <p class="text-display text-default">
              {{ firstVisits.total_appointments }}
            </p>
            <p class="text-caption text-subtle">
              {{ t('reports.scheduling.labels.excludingCancelled') }}
            </p>
          </div>
        </UCard>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Hours by Professional -->
        <UCard>
          <template #header>
            <h3 class="font-semibold text-default">
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
                  <p class="text-muted">
                    {{ prof.professional_name }}
                  </p>
                  <p class="text-caption text-subtle">
                    {{ prof.appointment_count }} {{ t('reports.scheduling.labels.appointments') }}
                  </p>
                </div>
              </div>
              <div class="text-right">
                <p class="font-semibold text-default">
                  {{ formatHours(prof.total_minutes) }}
                </p>
                <div class="flex items-center gap-2 text-caption text-subtle">
                  <span class="text-success-accent">{{ prof.completed_count }} ✓</span>
                  <span class="text-danger-accent">{{ prof.cancelled_count }} ✗</span>
                  <span class="text-warning-accent">{{ prof.no_show_count }} ⊘</span>
                </div>
              </div>
            </div>
          </div>
          <p
            v-else
            class="text-subtle text-center py-4"
          >
            {{ t('reports.billing.noData') }}
          </p>
        </UCard>

        <!-- Cabinet Utilization -->
        <UCard>
          <template #header>
            <h3 class="font-semibold text-default">
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
                  <p class="text-muted">
                    {{ cabinet.cabinet }}
                  </p>
                  <p class="text-caption text-subtle">
                    {{ cabinet.appointment_count }} {{ t('reports.scheduling.labels.appointments') }}
                  </p>
                </div>
              </div>
              <div class="text-right">
                <p class="font-semibold text-default">
                  {{ formatHours(cabinet.total_minutes) }}
                </p>
                <p class="text-caption text-subtle">
                  {{ cabinet.completed_count }} {{ t('reports.scheduling.labels.completed') }}
                </p>
              </div>
            </div>
          </div>
          <p
            v-else
            class="text-subtle text-center py-4"
          >
            {{ t('reports.billing.noData') }}
          </p>
        </UCard>

        <!-- Day of Week Distribution -->
        <UCard class="lg:col-span-2">
          <template #header>
            <div class="flex items-center justify-between">
              <h3 class="font-semibold text-default">
                {{ t('reports.scheduling.labels.byDayOfWeek') }}
              </h3>
              <!-- Legend -->
              <div class="flex items-center gap-4 text-xs">
                <div class="flex items-center gap-1">
                  <div class="w-3 h-3 rounded bg-[var(--color-success-accent)]" />
                  <span class="text-muted dark:text-subtle">{{ t('reports.scheduling.labels.completed') }}</span>
                </div>
                <div class="flex items-center gap-1">
                  <div class="w-3 h-3 rounded bg-[var(--color-danger-accent)]" />
                  <span class="text-muted dark:text-subtle">{{ t('reports.scheduling.labels.cancelled') }}</span>
                </div>
                <div class="flex items-center gap-1">
                  <div class="w-3 h-3 rounded bg-[var(--color-warning-accent)]" />
                  <span class="text-muted dark:text-subtle">{{ t('reports.scheduling.labels.noShows') }}</span>
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
              <div class="w-24 text-sm text-muted">
                {{ getDayOfWeekLabel(day.day_name) }}
              </div>
              <div class="flex-1">
                <div class="flex items-center gap-2">
                  <!-- Stacked bar container -->
                  <div
                    class="flex-1 bg-surface-sunken rounded-full h-4 overflow-hidden"
                  >
                    <div
                      class="flex h-4"
                      :style="{ width: `${(day.appointment_count / maxDayCount) * 100}%` }"
                    >
                      <!-- Completed (green) -->
                      <div
                        v-if="day.completed_count > 0"
                        class="bg-[var(--color-success-accent)] h-4 transition-all"
                        :style="{ width: `${(day.completed_count / day.appointment_count) * 100}%` }"
                        :title="`${day.completed_count} ${t('reports.scheduling.labels.completed')}`"
                      />
                      <!-- Cancelled (red) -->
                      <div
                        v-if="day.cancelled_count > 0"
                        class="bg-[var(--color-danger-accent)] h-4 transition-all"
                        :style="{ width: `${(day.cancelled_count / day.appointment_count) * 100}%` }"
                        :title="`${day.cancelled_count} ${t('reports.scheduling.labels.cancelled')}`"
                      />
                      <!-- No-show (amber) -->
                      <div
                        v-if="day.no_show_count > 0"
                        class="bg-[var(--color-warning-accent)] h-4 transition-all"
                        :style="{ width: `${(day.no_show_count / day.appointment_count) * 100}%` }"
                        :title="`${day.no_show_count} ${t('reports.scheduling.labels.noShows')}`"
                      />
                      <!-- Other statuses (gray) -->
                      <div
                        v-if="day.appointment_count - day.completed_count - day.cancelled_count - day.no_show_count > 0"
                        class="bg-[var(--color-text-subtle)] h-4 transition-all"
                        :style="{ width: `${((day.appointment_count - day.completed_count - day.cancelled_count - day.no_show_count) / day.appointment_count) * 100}%` }"
                        :title="`${day.appointment_count - day.completed_count - day.cancelled_count - day.no_show_count} ${t('reports.scheduling.labels.pending')}`"
                      />
                    </div>
                  </div>
                  <span class="text-sm font-medium w-12 text-right text-default">
                    {{ day.appointment_count }}
                  </span>
                </div>
              </div>
            </div>
          </div>
          <p
            v-else
            class="text-subtle text-center py-4"
          >
            {{ t('reports.billing.noData') }}
          </p>
        </UCard>
      </div>

      <!-- Status Breakdown (Additional Info) -->
      <UCard v-if="summary">
        <template #header>
          <h3 class="font-semibold text-default">
            {{ t('reports.scheduling.labels.statusBreakdown') }}
          </h3>
        </template>

        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
          <div class="text-center p-3 bg-surface-muted rounded-lg">
            <UIcon name="i-lucide-calendar" class="h-6 w-6 mx-auto text-subtle mb-1" />
            <p class="text-h1 text-default">{{ summary.scheduled }}</p>
            <p class="text-caption text-subtle">{{ t('appointments.status.scheduled') }}</p>
          </div>

          <div class="text-center p-3 bg-surface-muted rounded-lg">
            <UIcon name="i-lucide-calendar-check" class="h-6 w-6 mx-auto text-info-accent mb-1" />
            <p class="text-h1 text-default">{{ summary.confirmed }}</p>
            <p class="text-caption text-subtle">{{ t('appointments.status.confirmed') }}</p>
          </div>

          <div class="text-center p-3 bg-surface-muted rounded-lg">
            <UIcon name="i-lucide-door-open" class="h-6 w-6 mx-auto text-warning-accent mb-1" />
            <p class="text-h1 text-default">{{ summary.checked_in }}</p>
            <p class="text-caption text-subtle">{{ t('appointments.status.checked_in') }}</p>
          </div>

          <div class="text-center p-3 bg-surface-muted rounded-lg">
            <UIcon name="i-lucide-stethoscope" class="h-6 w-6 mx-auto text-warning-accent mb-1" />
            <p class="text-h1 text-default">{{ summary.in_treatment }}</p>
            <p class="text-caption text-subtle">{{ t('appointments.status.in_treatment') }}</p>
          </div>

          <div class="text-center p-3 bg-surface-muted rounded-lg">
            <UIcon name="i-lucide-check-circle" class="h-6 w-6 mx-auto text-success-accent mb-1" />
            <p class="text-h1 text-default">{{ summary.completed }}</p>
            <p class="text-caption text-subtle">{{ t('appointments.status.completed') }}</p>
          </div>

          <div class="text-center p-3 bg-surface-muted rounded-lg">
            <UIcon name="i-lucide-x-circle" class="h-6 w-6 mx-auto text-danger-accent mb-1" />
            <p class="text-h1 text-default">{{ summary.cancelled }}</p>
            <p class="text-caption text-subtle">{{ t('appointments.status.cancelled') }}</p>
          </div>

          <div class="text-center p-3 bg-surface-muted rounded-lg">
            <UIcon name="i-lucide-user-x" class="h-6 w-6 mx-auto text-warning-accent mb-1" />
            <p class="text-h1 text-default">{{ summary.no_show }}</p>
            <p class="text-caption text-subtle">{{ t('appointments.status.no_show') }}</p>
          </div>
        </div>
      </UCard>

      <!-- Funnel -->
      <UCard v-if="funnel">
        <template #header>
          <h3 class="text-h3 text-default">{{ t('reports.scheduling.analytics.funnel') }}</h3>
          <p class="text-caption text-subtle">{{ t('reports.scheduling.analytics.funnelDesc') }}</p>
        </template>
        <div class="space-y-2">
          <div v-for="row in funnelRows" :key="row.stage" class="flex items-center gap-3">
            <span class="w-32 text-ui text-default">{{ t(row.labelKey) }}</span>
            <div class="flex-1 bg-surface-muted rounded-full h-4 overflow-hidden">
              <div
                class="h-full bg-primary-500 transition-all"
                :style="{ width: `${row.widthPct}%` }"
              />
            </div>
            <span class="w-12 text-right text-ui text-default">{{ row.count }}</span>
          </div>
        </div>
        <template #footer>
          <div class="grid grid-cols-3 gap-4 text-center">
            <div>
              <p class="text-caption text-subtle">{{ t('reports.scheduling.analytics.completionRate') }}</p>
              <p class="text-h2 text-success-accent">{{ formatPercent(funnel.completion_rate) }}</p>
            </div>
            <div>
              <p class="text-caption text-subtle">{{ t('reports.scheduling.analytics.noShowRate') }}</p>
              <p class="text-h2 text-danger-accent">{{ formatPercent(funnel.no_show_rate) }}</p>
            </div>
            <div>
              <p class="text-caption text-subtle">{{ t('reports.scheduling.analytics.cancellationRate') }}</p>
              <p class="text-h2 text-subtle">{{ formatPercent(funnel.cancellation_rate) }}</p>
            </div>
          </div>
        </template>
      </UCard>

      <!-- Waiting times -->
      <UCard v-if="waitingStats">
        <template #header>
          <h3 class="text-h3 text-default">{{ t('reports.scheduling.analytics.waitingTimes') }}</h3>
          <p class="text-caption text-subtle">{{ t('reports.scheduling.analytics.waitingTimesDesc') }}</p>
        </template>
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
          <div class="text-center">
            <p class="text-caption text-subtle">{{ t('reports.scheduling.analytics.samples') }}</p>
            <p class="text-h1 text-default">{{ waitingStats.sample_size }}</p>
          </div>
          <div class="text-center">
            <p class="text-caption text-subtle">{{ t('reports.scheduling.analytics.average') }}</p>
            <p class="text-h1 text-default">{{ formatMinutes(waitingStats.avg_minutes) }}</p>
          </div>
          <div class="text-center">
            <p class="text-caption text-subtle">{{ t('reports.scheduling.analytics.median') }}</p>
            <p class="text-h1 text-default">{{ formatMinutes(waitingStats.median_minutes) }}</p>
          </div>
          <div class="text-center">
            <p class="text-caption text-subtle">{{ t('reports.scheduling.analytics.p90') }}</p>
            <p class="text-h1 text-default">{{ formatMinutes(waitingStats.p90_minutes) }}</p>
          </div>
        </div>
        <div v-if="waitingStats.sample_size > 0" class="space-y-2">
          <div
            v-for="bucket in waitingStats.distribution"
            :key="bucket.label"
            class="flex items-center gap-3"
          >
            <span class="w-20 text-ui text-default tnum">{{ bucket.label }} min</span>
            <div class="flex-1 bg-surface-muted rounded-full h-3 overflow-hidden">
              <div
                class="h-full bg-amber-500 transition-all"
                :style="{ width: `${(bucket.count / maxWaitBucket) * 100}%` }"
              />
            </div>
            <span class="w-10 text-right text-ui text-default">{{ bucket.count }}</span>
          </div>
        </div>
      </UCard>

      <!-- Punctuality -->
      <UCard v-if="punctuality">
        <template #header>
          <h3 class="text-h3 text-default">{{ t('reports.scheduling.analytics.punctuality') }}</h3>
          <p class="text-caption text-subtle">{{ t('reports.scheduling.analytics.punctualityDesc') }}</p>
        </template>
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
          <div class="text-center">
            <p class="text-caption text-subtle">{{ t('reports.scheduling.analytics.samples') }}</p>
            <p class="text-h1 text-default">{{ punctuality.sample_size }}</p>
          </div>
          <div class="text-center">
            <p class="text-caption text-subtle">{{ t('reports.scheduling.analytics.avgDelta') }}</p>
            <p class="text-h1 text-default">{{ formatSignedMinutes(punctuality.avg_delta_minutes) }}</p>
          </div>
          <div class="text-center">
            <p class="text-caption text-subtle">{{ t('reports.scheduling.analytics.medianDelta') }}</p>
            <p class="text-h1 text-default">{{ formatSignedMinutes(punctuality.median_delta_minutes) }}</p>
          </div>
          <div class="text-center">
            <p class="text-caption text-subtle">{{ t('reports.scheduling.analytics.onTime') }}</p>
            <p class="text-h1 text-success-accent">{{ formatPercent(punctuality.on_time_pct) }}</p>
          </div>
        </div>
        <div v-if="punctuality.sample_size > 0" class="space-y-2">
          <div
            v-for="bucket in punctuality.distribution"
            :key="bucket.label"
            class="flex items-center gap-3"
          >
            <span class="w-24 text-ui text-default tnum">{{ t(`reports.scheduling.analytics.punctuality_${bucket.label}`) }}</span>
            <div class="flex-1 bg-surface-muted rounded-full h-3 overflow-hidden">
              <div
                class="h-full bg-blue-500 transition-all"
                :style="{ width: `${(bucket.count / maxPunctualityBucket) * 100}%` }"
              />
            </div>
            <span class="w-10 text-right text-ui text-default">{{ bucket.count }}</span>
          </div>
        </div>
      </UCard>

      <!-- Duration variance -->
      <UCard v-if="durationVariance">
        <template #header>
          <h3 class="text-h3 text-default">{{ t('reports.scheduling.analytics.durationVariance') }}</h3>
          <p class="text-caption text-subtle">{{ t('reports.scheduling.analytics.durationVarianceDesc') }}</p>
        </template>
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div class="text-center">
            <p class="text-caption text-subtle">{{ t('reports.scheduling.analytics.samples') }}</p>
            <p class="text-h1 text-default">{{ durationVariance.sample_size }}</p>
          </div>
          <div class="text-center">
            <p class="text-caption text-subtle">{{ t('reports.scheduling.analytics.avgOverrun') }}</p>
            <p class="text-h1 text-default">{{ formatPercent(durationVariance.avg_overrun_pct) }}</p>
          </div>
          <div class="text-center">
            <p class="text-caption text-subtle">{{ t('reports.scheduling.analytics.overrunCount') }}</p>
            <p class="text-h1 text-warning-accent">{{ durationVariance.overrun_count }}</p>
          </div>
          <div class="text-center">
            <p class="text-caption text-subtle">{{ t('reports.scheduling.analytics.underCount') }}</p>
            <p class="text-h1 text-success-accent">{{ durationVariance.under_count }}</p>
          </div>
        </div>
      </UCard>
    </template>
  </div>
</template>
