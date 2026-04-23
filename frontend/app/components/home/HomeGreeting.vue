<script setup lang="ts">
const { t, locale } = useI18n()
const { user } = useAuth()
const { can } = usePermissions()

const now = ref(new Date())

function refreshNow() {
  now.value = new Date()
}

let intervalId: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  refreshNow()
  intervalId = setInterval(refreshNow, 60_000)
})

onBeforeUnmount(() => {
  if (intervalId) clearInterval(intervalId)
})

const greetingKey = computed(() => {
  const h = now.value.getHours()
  if (h < 6 || h >= 21) return 'dashboard.greetings.evening'
  if (h < 13) return 'dashboard.greetings.morning'
  return 'dashboard.greetings.afternoon'
})

const firstName = computed(() => user.value?.first_name?.trim() ?? '')

const title = computed(() => {
  const g = t(greetingKey.value)
  return firstName.value ? `${g}, ${firstName.value}` : g
})

const formattedDate = computed(() =>
  now.value.toLocaleDateString(locale.value, {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  })
)

const canWriteAppointments = computed(() => can('agenda.appointments.write'))
const canWritePatients = computed(() => can('patients.write'))
</script>

<template>
  <PageHeader
    :title="title"
    :subtitle="formattedDate"
  >
    <template #actions>
      <UButton
        v-if="canWritePatients"
        to="/patients?new=1"
        variant="soft"
        color="neutral"
        icon="i-lucide-user-plus"
      >
        {{ t('dashboard.quickActions.newPatient') }}
      </UButton>
      <UButton
        v-if="canWriteAppointments"
        to="/appointments?new=1"
        variant="solid"
        color="primary"
        icon="i-lucide-calendar-plus"
      >
        {{ t('dashboard.quickActions.newAppointment') }}
      </UButton>
    </template>
  </PageHeader>
</template>
