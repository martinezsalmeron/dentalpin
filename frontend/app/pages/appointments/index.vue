<script setup lang="ts">
const { t } = useI18n()

// Placeholder for Day 3 implementation
</script>

<template>
  <div class="space-y-6">
    <!-- Page header -->
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        {{ t('appointments.title') }}
      </h1>
      <UButton icon="i-lucide-plus">
        {{ t('appointments.create') }}
      </UButton>
    </div>

    <!-- Placeholder content -->
    <UCard>
      <div class="text-center py-16">
        <UIcon
          name="i-lucide-calendar"
          class="w-16 h-16 text-gray-400 mx-auto mb-4"
        />
        <h2 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
          Calendario de citas
        </h2>
        <p class="text-gray-500 dark:text-gray-400">
          El calendario semanal se implementará en el Día 3
        </p>
      </div>
    </UCard>
  </div>
</template>
