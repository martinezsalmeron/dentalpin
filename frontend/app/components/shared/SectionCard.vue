<script setup lang="ts">
/**
 * SectionCard — UCard + consistent icon/title/actions header.
 *
 * Use this anywhere the pattern is:
 *   <UCard><template #header><icon/><title/><actions/></template>...<footer/></UCard>
 *
 * Slots:
 *   default      — body content
 *   actions      — header-right actions (buttons, toggles)
 *   subtitle     — small meta text below title
 *   footer       — footer bar
 */
interface Props {
  /** Header icon (Lucide name) */
  icon?: string
  /** Colour role for the icon — defaults to primary */
  iconRole?: 'primary' | 'success' | 'info' | 'warning' | 'danger' | 'neutral'
  title?: string
  /** Hide the header entirely */
  noHeader?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  iconRole: 'primary',
  noHeader: false
})

const iconColorVar = computed(() => {
  const map = {
    primary: '--color-primary',
    success: '--color-success-accent',
    info: '--color-info-accent',
    warning: '--color-warning-accent',
    danger: '--color-danger-accent',
    neutral: '--color-text-muted'
  } as const
  return `var(${map[props.iconRole]})`
})
</script>

<template>
  <UCard>
    <template
      v-if="!noHeader && (title || icon || $slots.actions || $slots.subtitle)"
      #header
    >
      <div class="flex items-center justify-between gap-3">
        <div class="flex items-center gap-2 min-w-0">
          <UIcon
            v-if="icon"
            :name="icon"
            class="w-4 h-4 shrink-0"
            :style="{ color: iconColorVar }"
          />
          <div class="min-w-0">
            <h2
              v-if="title"
              class="text-h3 text-default truncate"
            >
              {{ title }}
            </h2>
            <div
              v-if="$slots.subtitle"
              class="text-caption text-muted"
            >
              <slot name="subtitle" />
            </div>
          </div>
        </div>
        <div
          v-if="$slots.actions"
          class="flex items-center gap-2 shrink-0"
        >
          <slot name="actions" />
        </div>
      </div>
    </template>

    <slot />

    <template
      v-if="$slots.footer"
      #footer
    >
      <slot name="footer" />
    </template>
  </UCard>
</template>
