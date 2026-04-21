<script setup lang="ts">
const { t } = useI18n()
const { can, canAny } = usePermissions()

const canReadClinic = computed(() => can('schedules.clinic_hours.read'))
const canReadProfessional = computed(() =>
  canAny(['schedules.professional.read', 'schedules.professional.own.read'])
)
</script>

<template>
  <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
    <UCard v-if="canReadClinic" class="hover:shadow-md transition">
      <div class="flex items-start gap-4">
        <UIcon name="i-lucide-building-2" class="text-primary-500 text-3xl" />
        <div class="flex-1">
          <h3 class="text-lg font-semibold mb-1">
            {{ t('schedules.settingsCards.clinicHoursTitle') }}
          </h3>
          <p class="text-gray-500 text-sm mb-3">
            {{ t('schedules.settingsCards.clinicHoursDescription') }}
          </p>
          <UButton
            to="/settings/clinic-hours"
            size="sm"
            variant="soft"
            icon="i-lucide-arrow-right"
          >
            {{ t('schedules.settingsCards.open') }}
          </UButton>
        </div>
      </div>
    </UCard>

    <UCard v-if="canReadProfessional" class="hover:shadow-md transition">
      <div class="flex items-start gap-4">
        <UIcon name="i-lucide-user-cog" class="text-primary-500 text-3xl" />
        <div class="flex-1">
          <h3 class="text-lg font-semibold mb-1">
            {{ t('schedules.settingsCards.professionalHoursTitle') }}
          </h3>
          <p class="text-gray-500 text-sm mb-3">
            {{ t('schedules.settingsCards.professionalHoursDescription') }}
          </p>
          <UButton
            to="/settings/professional-schedules"
            size="sm"
            variant="soft"
            icon="i-lucide-arrow-right"
          >
            {{ t('schedules.settingsCards.open') }}
          </UButton>
        </div>
      </div>
    </UCard>
  </div>
</template>
