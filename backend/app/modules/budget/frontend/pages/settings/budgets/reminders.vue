<script setup lang="ts">
definePageMeta({ middleware: ['auth'] })

const { t } = useI18n()
const { settings, loading, saving, fetch, update } = useBudgetSettings()

const remindersEnabled = ref(false)

watch(settings, (s) => {
  if (s) remindersEnabled.value = s.budget_reminders_enabled
})

onMounted(fetch)

async function save() {
  await update({ budget_reminders_enabled: remindersEnabled.value })
}
</script>

<template>
  <UContainer class="py-8 max-w-2xl space-y-6">
    <header class="space-y-2">
      <NuxtLink to="/settings/budgets" class="text-sm text-[var(--ui-primary)] inline-flex items-center gap-1">
        <UIcon name="i-lucide-arrow-left" class="w-4 h-4" /> {{ t('budget.settings.title') }}
      </NuxtLink>
      <h1 class="text-2xl font-semibold">{{ t('budget.settings.cards.reminders.title') }}</h1>
    </header>

    <UCard v-if="!loading">
      <div class="space-y-4">
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="font-medium">{{ t('budget.settings.reminders.enabled') }}</p>
            <p class="text-xs text-[var(--ui-text-muted)] mt-1 max-w-xl">
              {{ t('budget.settings.reminders.enabledHelp') }}
            </p>
          </div>
          <USwitch v-model="remindersEnabled" />
        </div>
      </div>
      <template #footer>
        <div class="flex justify-end">
          <UButton color="primary" :loading="saving" @click="save">
            {{ t('budget.settings.reminders.save') }}
          </UButton>
        </div>
      </template>
    </UCard>
  </UContainer>
</template>
