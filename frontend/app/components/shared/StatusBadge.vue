<script setup lang="ts">
import type { SemanticRole } from '~/config/severity'
import { roleToUiColor } from '~/config/severity'

interface Props {
  /** Semantic role — determines colour */
  role: SemanticRole
  /** Visible label */
  label: string
  /** Show a leading accent dot (for emphasis without saturating the fill — DESIGN §6.4) */
  dot?: boolean
  /** Optional icon name, rendered in accent colour */
  icon?: string
  /** Optional trailing icon (e.g. external-link, chevron — signals clickable) */
  trailingIcon?: string
  size?: 'xs' | 'sm' | 'md'
}

const props = withDefaults(defineProps<Props>(), {
  size: 'sm',
  dot: false
})

const uiColor = computed(() => roleToUiColor(props.role))

const accentVar = computed(() => {
  // map role → CSS var name
  const map: Record<SemanticRole, string> = {
    primary: '--color-primary',
    success: '--color-success-accent',
    info: '--color-info-accent',
    warning: '--color-warning-accent',
    danger: '--color-danger-accent',
    neutral: '--color-text-muted'
  }
  return `var(${map[props.role]})`
})
</script>

<template>
  <UBadge
    :color="uiColor"
    :size="size"
    variant="subtle"
    class="gap-1"
  >
    <span
      v-if="dot"
      class="inline-block w-1.5 h-1.5 rounded-full shrink-0"
      :style="{ backgroundColor: accentVar }"
      aria-hidden="true"
    />
    <UIcon
      v-if="icon"
      :name="icon"
      class="w-3 h-3 shrink-0"
      :style="{ color: accentVar }"
    />
    {{ label }}
    <UIcon
      v-if="trailingIcon"
      :name="trailingIcon"
      class="w-3 h-3 shrink-0"
      :style="{ color: accentVar }"
      aria-hidden="true"
    />
  </UBadge>
</template>
