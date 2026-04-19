<script setup lang="ts">
/**
 * SectionHeader — standard section heading with optional icon and action.
 *
 * Visual anatomy:
 *   [icon] [title]                              [action]
 *
 * Props:
 *   icon  — Lucide icon name (skipped if absent)
 *   title — text shown as <h3>; or override via default slot
 *
 * Slots:
 *   default — replaces title text
 *   action  — right-side action (button, toggle, etc.)
 */
interface Props {
  icon?: string
  title?: string
}

defineProps<Props>()
</script>

<template>
  <div class="flex items-center justify-between gap-[var(--density-gap,0.75rem)]">
    <h3 class="font-medium flex items-center gap-2 min-w-0">
      <UIcon
        v-if="icon"
        :name="icon"
        class="icon-density shrink-0"
      />
      <template v-if="$slots.default">
        <slot />
      </template>
      <span
        v-else
        class="truncate"
      >{{ title }}</span>
    </h3>
    <div
      v-if="$slots.action"
      class="shrink-0 flex items-center gap-2"
    >
      <slot name="action" />
    </div>
  </div>
</template>
