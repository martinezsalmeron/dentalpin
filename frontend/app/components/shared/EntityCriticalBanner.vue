<script setup lang="ts">
import type { SemanticRole } from '~/config/severity'
import { roleToUiColor } from '~/config/severity'

interface Cta {
  label: string
  onClick: () => void
  icon?: string
}

interface Props {
  role: SemanticRole
  title: string
  description?: string
  icon?: string
  cta?: Cta
  dismissible?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  dismissible: false
})

const emit = defineEmits<{ dismiss: [] }>()

const { t } = useI18n()

const visible = ref(true)

function dismiss() {
  visible.value = false
  emit('dismiss')
}

const containerClass = computed(() => {
  const role = props.role
  const map: Record<SemanticRole, string> = {
    primary: 'bg-primary-50 border-primary-200 text-primary-900 dark:bg-primary-950/40 dark:border-primary-800 dark:text-primary-100',
    success: 'bg-success-50 border-success-200 text-success-900 dark:bg-success-950/40 dark:border-success-800 dark:text-success-100',
    info: 'bg-info-50 border-info-200 text-info-900 dark:bg-info-950/40 dark:border-info-800 dark:text-info-100',
    warning: 'bg-warning-50 border-warning-200 text-warning-900 dark:bg-warning-950/40 dark:border-warning-800 dark:text-warning-100',
    danger: 'bg-error-50 border-error-200 text-error-900 dark:bg-error-950/40 dark:border-error-800 dark:text-error-100',
    neutral: 'bg-elevated border-default text-default'
  }
  return map[role]
})

const ctaColor = computed(() => roleToUiColor(props.role))
const defaultIcon = computed(() => props.icon ?? iconFor(props.role))

function iconFor(role: SemanticRole): string {
  const map: Record<SemanticRole, string> = {
    primary: 'i-lucide-info',
    success: 'i-lucide-check-circle-2',
    info: 'i-lucide-info',
    warning: 'i-lucide-alert-triangle',
    danger: 'i-lucide-alert-octagon',
    neutral: 'i-lucide-info'
  }
  return map[role]
}
</script>

<template>
  <div
    v-if="visible"
    role="alert"
    class="rounded-lg border px-4 py-3 flex items-start gap-3"
    :class="containerClass"
  >
    <UIcon
      :name="defaultIcon"
      class="w-5 h-5 mt-0.5 shrink-0"
      aria-hidden="true"
    />

    <div class="min-w-0 flex-1">
      <p class="text-body font-semibold">
        {{ title }}
      </p>
      <p
        v-if="description"
        class="text-body-sm mt-0.5"
      >
        {{ description }}
      </p>
    </div>

    <div class="flex items-center gap-2 shrink-0">
      <UButton
        v-if="cta"
        :color="ctaColor"
        :icon="cta.icon"
        size="sm"
        @click="cta.onClick"
      >
        {{ cta.label }}
      </UButton>
      <UButton
        v-if="dismissible"
        variant="ghost"
        color="neutral"
        icon="i-lucide-x"
        size="sm"
        :aria-label="t('shared.criticalBanner.dismiss')"
        @click="dismiss"
      />
    </div>
  </div>
</template>
