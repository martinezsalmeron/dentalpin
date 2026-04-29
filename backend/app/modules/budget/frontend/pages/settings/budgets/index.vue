<script setup lang="ts">
/**
 * /settings/budgets — entry grid for the budget-related clinic
 * settings. Each card links to a dedicated form sub-page.
 */

definePageMeta({ middleware: ['auth'] })

const { t } = useI18n()

const cards = [
  {
    key: 'expiry',
    icon: 'i-lucide-calendar-clock',
    to: '/settings/budgets/expiry',
  },
  {
    key: 'reminders',
    icon: 'i-lucide-bell',
    to: '/settings/budgets/reminders',
  },
  {
    key: 'publicLink',
    icon: 'i-lucide-shield-check',
    to: '/settings/budgets/public-link',
  },
] as const
</script>

<template>
  <UContainer class="py-8 space-y-6">
    <header>
      <h1 class="text-2xl font-semibold">{{ t('budget.settings.title') }}</h1>
      <p class="text-sm text-[var(--ui-text-muted)] mt-1">
        {{ t('budget.settings.description') }}
      </p>
    </header>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <UCard
        v-for="card in cards"
        :key="card.key"
        class="transition-colors hover:border-[var(--ui-primary)]"
      >
        <NuxtLink :to="card.to" class="block space-y-3">
          <div class="flex items-center gap-3">
            <UIcon :name="card.icon" class="w-6 h-6 text-[var(--ui-primary)]" />
            <h2 class="font-semibold">
              {{ t(`budget.settings.cards.${card.key}.title`) }}
            </h2>
          </div>
          <p class="text-sm text-[var(--ui-text-muted)]">
            {{ t(`budget.settings.cards.${card.key}.description`) }}
          </p>
        </NuxtLink>
      </UCard>
    </div>
  </UContainer>
</template>
