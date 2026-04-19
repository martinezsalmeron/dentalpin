<script setup lang="ts">
/**
 * FilterChip — selectable chip for filter bars.
 * Selected state shows strong ring; unselected dims the chip.
 * Supports a colour dot (cabinet) or a coloured initials avatar (professional).
 */
interface Props {
  label: string
  selected: boolean
  /** Optional colour swatch (hex) */
  color?: string
  /** Initials (e.g., for professional avatars). If provided with color, renders an avatar disc */
  initials?: string
}

defineProps<Props>()

defineEmits<{
  toggle: []
}>()
</script>

<template>
  <button
    type="button"
    class="flex items-center gap-1.5 px-2 py-1 rounded-token-sm text-ui transition-opacity"
    :class="selected
      ? 'bg-surface-muted text-default ring-1 ring-[var(--color-border-strong)]'
      : 'text-muted opacity-60 hover:opacity-100'"
    @click="$emit('toggle')"
  >
    <span
      v-if="initials && color"
      class="w-5 h-5 rounded-full flex items-center justify-center text-white text-[10px] font-semibold shrink-0"
      :style="{ backgroundColor: color }"
    >
      {{ initials }}
    </span>
    <span
      v-else-if="color"
      class="w-2.5 h-2.5 rounded-full shrink-0"
      :style="{ backgroundColor: color }"
    />
    <span>{{ label }}</span>
  </button>
</template>
