<script setup lang="ts">
const { t } = useI18n()
const { can } = usePermissions()

const reportCategories = computed(() => [
  {
    key: 'billing',
    label: t('reports.billing.title'),
    description: t('reports.billing.description'),
    icon: 'i-lucide-receipt',
    to: '/reports/billing',
    permission: 'reports.billing.read',
    color: 'text-success-accent'
  },
  {
    key: 'budgets',
    label: t('reports.budgets.title'),
    description: t('reports.budgets.description'),
    icon: 'i-lucide-file-text',
    to: '/reports/budgets',
    permission: 'reports.budgets.read',
    color: 'text-info-accent'
  },
  {
    key: 'scheduling',
    label: t('reports.scheduling.title'),
    description: t('reports.scheduling.description'),
    icon: 'i-lucide-calendar-check',
    to: '/reports/scheduling',
    permission: 'reports.scheduling.read',
    color: 'text-purple-600'
  }
])

const visibleCategories = computed(() =>
  reportCategories.value.filter(cat => can(cat.permission))
)
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-display text-default">
        {{ t('reports.title') }}
      </h1>
      <p class="text-muted mt-1">
        {{ t('reports.subtitle') }}
      </p>
    </div>

    <!-- Report Categories Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <UCard
        v-for="category in visibleCategories"
        :key="category.key"
        :class="[
          'transition-all hover:shadow-lg',
          category.comingSoon ? 'opacity-60' : 'cursor-pointer hover:scale-[1.02]'
        ]"
        @click="!category.comingSoon && navigateTo(category.to)"
      >
        <div class="flex flex-col items-center text-center space-y-4 py-4">
          <div
            class="p-4 rounded-full bg-surface-muted"
          >
            <UIcon
              :name="category.icon"
              :class="['h-8 w-8', category.color]"
            />
          </div>

          <div>
            <h3 class="text-h1 text-default flex items-center justify-center gap-2">
              {{ category.label }}
              <UBadge
                v-if="category.comingSoon"
                color="neutral"
                size="xs"
              >
                {{ t('common.comingSoon') }}
              </UBadge>
            </h3>
            <p class="text-caption text-subtle mt-1">
              {{ category.description }}
            </p>
          </div>

          <UButton
            v-if="!category.comingSoon"
            variant="soft"
            trailing-icon="i-lucide-arrow-right"
            @click.stop="navigateTo(category.to)"
          >
            {{ t('reports.viewReports') }}
          </UButton>
        </div>
      </UCard>
    </div>

    <!-- Empty state if no permissions -->
    <div
      v-if="visibleCategories.length === 0"
      class="text-center py-12"
    >
      <UIcon
        name="i-lucide-lock"
        class="h-12 w-12 text-subtle mx-auto mb-4"
      />
      <p class="text-subtle">
        {{ t('reports.noAccess') }}
      </p>
    </div>
  </div>
</template>
