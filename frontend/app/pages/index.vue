<script setup lang="ts">
import type { Appointment, Patient, PaginatedResponse } from '~/types'

const { t } = useI18n()
const api = useApi()

const { data: appointmentsData, status: appointmentsStatus } = await useAsyncData(
  'dashboard:appointments',
  async () => {
    const today = new Date()
    const startOfDay = new Date(today.getFullYear(), today.getMonth(), today.getDate()).toISOString()
    const endOfDay = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 23, 59, 59).toISOString()
    try {
      return await api.get<PaginatedResponse<Appointment>>(
        `/api/v1/agenda/appointments?start_date=${startOfDay}&end_date=${endOfDay}`
      )
    } catch {
      return { data: [], total: 0, page: 1, page_size: 20 }
    }
  }
)

const { data: patientsData, status: patientsStatus } = await useAsyncData(
  'dashboard:patients',
  async () => {
    try {
      return await api.get<PaginatedResponse<Patient>>(
        '/api/v1/patients?page_size=5&sort=-created_at'
      )
    } catch {
      return { data: [], total: 0, page: 1, page_size: 5 }
    }
  }
)

const todayAppointments = computed(() => appointmentsData.value?.data || [])
const recentPatients = computed(() => patientsData.value?.data || [])

const nextAppointment = computed(() => {
  const now = new Date()
  return todayAppointments.value
    .filter(apt => new Date(apt.start_time) > now && apt.status !== 'cancelled')
    .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())[0]
})

function formatTime(dateStr: string): string {
  return new Date(dateStr).toLocaleTimeString('es-ES', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

const isEmpty = computed(() =>
  todayAppointments.value.length === 0 && recentPatients.value.length === 0
)
</script>

<template>
  <div>
    <PageHeader :title="t('dashboard.title')" />

    <!-- Empty state for first-time users -->
    <UCard v-if="isEmpty && appointmentsStatus === 'success' && patientsStatus === 'success'">
      <EmptyState
        icon="i-lucide-smile"
        :title="t('dashboard.welcome')"
        :description="t('dashboard.welcomeMessage')"
      >
        <template #actions>
          <UButton
            to="/patients"
            color="primary"
            variant="soft"
            icon="i-lucide-plus"
          >
            {{ t('patients.emptyAction') }}
          </UButton>
        </template>
      </EmptyState>
    </UCard>

    <!-- Widgets -->
    <div
      v-else
      class="grid grid-cols-1 md:grid-cols-2 gap-5"
    >
      <!-- Today's appointments -->
      <SectionCard
        icon="i-lucide-calendar"
        :title="t('dashboard.todayAppointments')"
      >
        <div
          v-if="appointmentsStatus === 'pending'"
          class="space-y-3"
        >
          <USkeleton class="h-4 w-24" />
          <USkeleton class="h-12 w-full" />
        </div>

        <EmptyState
          v-else-if="todayAppointments.length === 0"
          icon="i-lucide-calendar-x"
          :title="t('dashboard.noAppointmentsToday')"
        />

        <div
          v-else
          class="space-y-4"
        >
          <p class="text-display tnum text-default">
            {{ todayAppointments.length }}
            <span class="text-body text-muted font-normal">
              {{ t('dashboard.appointmentsCount', todayAppointments.length) }}
            </span>
          </p>

          <div
            v-if="nextAppointment"
            class="alert-surface-primary rounded-token-md px-3 py-2"
          >
            <p class="text-caption mb-1">
              {{ t('dashboard.nextAppointment') }}
            </p>
            <div class="flex items-center justify-between">
              <span class="text-ui tnum">
                {{ formatTime(nextAppointment.start_time) }}
              </span>
              <span class="text-body">
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
      </SectionCard>

      <!-- Recent patients -->
      <SectionCard
        icon="i-lucide-users"
        :title="t('dashboard.recentPatients')"
      >
        <div
          v-if="patientsStatus === 'pending'"
          class="space-y-3"
        >
          <USkeleton
            v-for="i in 3"
            :key="i"
            class="h-10 w-full"
          />
        </div>

        <EmptyState
          v-else-if="recentPatients.length === 0"
          icon="i-lucide-users"
          :title="t('patients.empty')"
        />

        <ul
          v-else
          class="divide-y divide-[var(--color-border-subtle)]"
        >
          <li
            v-for="patient in recentPatients"
            :key="patient.id"
          >
            <ListRow :to="`/patients/${patient.id}`">
              <template #leading>
                <UAvatar
                  :alt="patient.first_name"
                  size="sm"
                />
              </template>
              <template #title>
                {{ patient.first_name }} {{ patient.last_name }}
              </template>
              <template #subtitle>
                {{ patient.phone || patient.email || '—' }}
              </template>
            </ListRow>
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
      </SectionCard>
    </div>

    <!-- Extension point for module-provided dashboard widgets. -->
    <ModuleSlot name="dashboard.widgets" :ctx="{}" />
  </div>
</template>
