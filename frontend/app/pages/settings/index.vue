<script setup lang="ts">
const { t } = useI18n()
const auth = useAuth()
const clinic = useClinic()
</script>

<template>
  <div class="space-y-6">
    <!-- Page header -->
    <div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        {{ t('settings.title') }}
      </h1>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Clinic info -->
      <UCard>
        <template #header>
          <div class="flex items-center gap-2">
            <UIcon name="i-lucide-building-2" class="w-5 h-5 text-primary-500" />
            <h2 class="font-semibold text-gray-900 dark:text-white">
              {{ t('settings.clinic') }}
            </h2>
          </div>
        </template>

        <div v-if="clinic.isLoading.value" class="space-y-3">
          <USkeleton class="h-4 w-24" />
          <USkeleton class="h-4 w-48" />
        </div>

        <div v-else-if="clinic.currentClinic.value" class="space-y-4">
          <div>
            <label class="text-sm font-medium text-gray-500 dark:text-gray-400">
              {{ t('settings.clinicName') }}
            </label>
            <p class="text-gray-900 dark:text-white">
              {{ clinic.currentClinic.value.name }}
            </p>
          </div>

          <div>
            <label class="text-sm font-medium text-gray-500 dark:text-gray-400">
              {{ t('settings.cabinets') }}
            </label>
            <div class="flex flex-wrap gap-2 mt-1">
              <UBadge
                v-for="cabinet in clinic.cabinets.value"
                :key="cabinet.name"
                variant="subtle"
                :style="{ backgroundColor: cabinet.color + '20', color: cabinet.color }"
              >
                {{ cabinet.name }}
              </UBadge>
              <span
                v-if="clinic.cabinets.value.length === 0"
                class="text-gray-500 dark:text-gray-400"
              >
                -
              </span>
            </div>
          </div>
        </div>

        <div v-else class="text-gray-500 dark:text-gray-400">
          {{ t('common.noData') }}
        </div>
      </UCard>

      <!-- User profile -->
      <UCard>
        <template #header>
          <div class="flex items-center gap-2">
            <UIcon name="i-lucide-user" class="w-5 h-5 text-primary-500" />
            <h2 class="font-semibold text-gray-900 dark:text-white">
              {{ t('settings.profile') }}
            </h2>
          </div>
        </template>

        <div v-if="auth.user.value" class="space-y-4">
          <div class="flex items-center gap-4">
            <UAvatar
              :alt="auth.user.value.first_name"
              size="lg"
            />
            <div>
              <p class="font-medium text-gray-900 dark:text-white">
                {{ auth.user.value.first_name }} {{ auth.user.value.last_name }}
              </p>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                {{ auth.user.value.email }}
              </p>
            </div>
          </div>
        </div>
      </UCard>
    </div>
  </div>
</template>
