<script setup lang="ts">
import type { Appointment, Patient, PaginatedResponse } from '~/types'

const { t } = useI18n()
const api = useApi()

// Fetch today's appointments
const { data: appointmentsData, status: appointmentsStatus } = await useAsyncData(
  'dashboard:appointments',
  async () => {
    const today = new Date()
    const startOfDay = new Date(today.getFullYear(), today.getMonth(), today.getDate()).toISOString()
    const endOfDay = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 23, 59, 59).toISOString()

    try {
      return await api.get<PaginatedResponse<Appointment>>(
        `/api/v1/clinical/appointments/?start_date=${startOfDay}&end_date=${endOfDay}`
      )
    }
    catch {
      return { data: [], total: 0, page: 1, page_size: 20 }
    }
  }
)

// Fetch recent patients
const { data: patientsData, status: patientsStatus } = await useAsyncData(
  'dashboard:patients',
  async () => {
    try {
      return await api.get<PaginatedResponse<Patient>>(
        '/api/v1/clinical/patients/?page_size=5&sort=-created_at'
      )
    }
    catch {
      return { data: [], total: 0, page: 1, page_size: 5 }
    }
  }
)

const todayAppointments = computed(() => appointmentsData.value?.data || [])
const recentPatients = computed(() => patientsData.value?.data || [])

// Get next appointment
const nextAppointment = computed(() => {
  const now = new Date()
  return todayAppointments.value
    .filter(apt => new Date(apt.start_time) > now && apt.status !== 'cancelled')
    .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())[0]
})

// Format time
function formatTime(dateStr: string): string {
  return new Date(dateStr).toLocaleTimeString('es-ES', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Check if dashboard is empty (no data)
const isEmpty = computed(() =>
  todayAppointments.value.length === 0 && recentPatients.value.length === 0
)
</script>

<template>
  <div class="space-y-6">
    <!-- Page header -->
    <div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        {{ t('dashboard.title') }}
      </h1>
    </div>

    <!-- Empty state for first-time users -->
    <UCard v-if="isEmpty && appointmentsStatus === 'success' && patientsStatus === 'success'">
      <div class="text-center py-8">
        <UIcon name="i-lucide-smile" class="w-12 h-12 text-primary-500 mx-auto mb-4" />
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          {{ t('dashboard.welcome') }}
        </h2>
        <p class="text-gray-500 dark:text-gray-400 mb-6">
          {{ t('dashboard.welcomeMessage') }}
        </p>
        <UButton
          to="/patients"
          icon="i-lucide-plus"
        >
          {{ t('patients.emptyAction') }}
        </UButton>
      </div>
    </UCard>

    <!-- Dashboard widgets -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Today's appointments -->
      <UCard>
        <template #header>
          <div class="flex items-center gap-2">
            <UIcon name="i-lucide-calendar" class="w-5 h-5 text-primary-500" />
            <h2 class="font-semibold text-gray-900 dark:text-white">
              {{ t('dashboard.todayAppointments') }}
            </h2>
          </div>
        </template>

        <div v-if="appointmentsStatus === 'pending'" class="space-y-3">
          <USkeleton class="h-4 w-24" />
          <USkeleton class="h-12 w-full" />
        </div>

        <div v-else-if="todayAppointments.length === 0" class="text-center py-4">
          <UIcon name="i-lucide-calendar-x" class="w-8 h-8 text-gray-400 mx-auto mb-2" />
          <p class="text-sm text-gray-500 dark:text-gray-400">
            {{ t('dashboard.noAppointmentsToday') }}
          </p>
        </div>

        <div v-else class="space-y-4">
          <!-- Appointment count -->
          <p class="text-3xl font-bold text-gray-900 dark:text-white">
            {{ todayAppointments.length }}
            <span class="text-base font-normal text-gray-500">
              {{ t('dashboard.appointmentsCount', todayAppointments.length) }}
            </span>
          </p>

          <!-- Next appointment -->
          <div v-if="nextAppointment" class="p-3 rounded-lg bg-primary-50 dark:bg-primary-950">
            <p class="text-xs text-primary-600 dark:text-primary-400 mb-1">
              {{ t('dashboard.nextAppointment') }}
            </p>
            <div class="flex items-center justify-between">
              <span class="font-medium text-gray-900 dark:text-white">
                {{ formatTime(nextAppointment.start_time) }}
              </span>
              <span class="text-sm text-gray-600 dark:text-gray-300">
                {{ nextAppointment.patient?.first_name }} {{ nextAppointment.patient?.last_name }}
              </span>
            </div>
          </div>
        </div>

        <template #footer>
          <UButton
            to="/appointments"
            variant="ghost"
            color="neutral"
            block
            trailing-icon="i-lucide-arrow-right"
          >
            {{ t('nav.appointments') }}
          </UButton>
        </template>
      </UCard>

      <!-- Recent patients -->
      <UCard>
        <template #header>
          <div class="flex items-center gap-2">
            <UIcon name="i-lucide-users" class="w-5 h-5 text-primary-500" />
            <h2 class="font-semibold text-gray-900 dark:text-white">
              {{ t('dashboard.recentPatients') }}
            </h2>
          </div>
        </template>

        <div v-if="patientsStatus === 'pending'" class="space-y-3">
          <USkeleton v-for="i in 3" :key="i" class="h-10 w-full" />
        </div>

        <div v-else-if="recentPatients.length === 0" class="text-center py-4">
          <UIcon name="i-lucide-users" class="w-8 h-8 text-gray-400 mx-auto mb-2" />
          <p class="text-sm text-gray-500 dark:text-gray-400">
            {{ t('patients.empty') }}
          </p>
        </div>

        <ul v-else class="divide-y divide-gray-200 dark:divide-gray-800">
          <li
            v-for="patient in recentPatients"
            :key="patient.id"
            class="py-2"
          >
            <NuxtLink
              :to="`/patients/${patient.id}`"
              class="flex items-center gap-3 hover:bg-gray-50 dark:hover:bg-gray-800 -mx-2 px-2 py-1 rounded-lg transition-colors"
            >
              <UAvatar
                :alt="patient.first_name"
                size="sm"
              />
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-gray-900 dark:text-white truncate">
                  {{ patient.first_name }} {{ patient.last_name }}
                </p>
                <p class="text-xs text-gray-500 dark:text-gray-400 truncate">
                  {{ patient.phone || patient.email || '-' }}
                </p>
              </div>
              <UIcon name="i-lucide-chevron-right" class="w-4 h-4 text-gray-400" />
            </NuxtLink>
          </li>
        </ul>

        <template #footer>
          <UButton
            to="/patients"
            variant="ghost"
            color="neutral"
            block
            trailing-icon="i-lucide-arrow-right"
          >
            {{ t('nav.patients') }}
          </UButton>
        </template>
      </UCard>
    </div>
  </div>
</template>
