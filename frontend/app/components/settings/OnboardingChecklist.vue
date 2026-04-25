<script setup lang="ts">
/**
 * Contextual onboarding checklist. Shown at the top of the settings
 * landing for clinics that still have setup tasks open. Items come
 * from :composable:`useSettingsRegistry` getting-started rules — the
 * host registers a baseline (clinic info, cabinets, billing readiness),
 * modules can add more.
 *
 * Dismissal persists in localStorage by clinic id; if items regress
 * (e.g. tax ID gets cleared) and the clinic is no longer fully set up,
 * the panel re-appears next session.
 */
const { t } = useI18n()
const registry = useSettingsRegistry()

const items = computed(() => registry.gettingStarted.value)
const isVisible = computed(() => items.value.length > 0 && !registry.isOnboardingDismissed.value)

function severityIcon(sev?: string): string {
  if (sev === 'critical') return 'i-lucide-alert-triangle'
  if (sev === 'warning') return 'i-lucide-alert-circle'
  return 'i-lucide-circle-check'
}

function severityColor(sev?: string): string {
  if (sev === 'critical') return 'var(--color-danger-accent)'
  if (sev === 'warning') return 'var(--color-warning-accent)'
  return 'var(--color-info-accent)'
}
</script>

<template>
  <section
    v-if="isVisible"
    class="rounded-[var(--radius-lg)] ring-1 ring-[var(--color-border)] bg-(--color-surface) p-4 sm:p-5"
  >
    <header class="flex items-start justify-between gap-3 mb-3">
      <div class="flex items-center gap-2 min-w-0">
        <UIcon
          name="i-lucide-rocket"
          class="w-5 h-5 text-(--color-primary-accent) shrink-0"
        />
        <div class="min-w-0">
          <h2 class="text-h3 text-default">
            {{ t('settings.onboarding.title') }}
          </h2>
          <p class="text-caption text-muted">
            {{ t('settings.onboarding.subtitle', { count: items.length }) }}
          </p>
        </div>
      </div>
      <UButton
        icon="i-lucide-x"
        size="xs"
        variant="ghost"
        color="neutral"
        :aria-label="t('settings.onboarding.dismiss')"
        @click="registry.dismissOnboarding()"
      >
        {{ t('settings.onboarding.dismiss') }}
      </UButton>
    </header>

    <ul class="divide-y divide-[var(--color-border-subtle)]">
      <li
        v-for="item in items"
        :key="item.id"
      >
        <NuxtLink
          :to="item.to"
          class="flex items-center gap-3 py-3 hover:bg-(--color-surface-muted) -mx-2 px-2 rounded-md transition min-h-[44px]"
        >
          <UIcon
            :name="item.icon ?? severityIcon(item.severity)"
            class="w-5 h-5 shrink-0"
            :style="{ color: severityColor(item.severity) }"
          />
          <div class="min-w-0 flex-1">
            <p class="text-body text-default">
              {{ t(item.labelKey) }}
            </p>
            <p
              v-if="item.descriptionKey"
              class="text-caption text-muted truncate"
            >
              {{ t(item.descriptionKey) }}
            </p>
          </div>
          <UIcon
            name="i-lucide-chevron-right"
            class="w-5 h-5 shrink-0 text-subtle"
          />
        </NuxtLink>
      </li>
    </ul>
  </section>
</template>
