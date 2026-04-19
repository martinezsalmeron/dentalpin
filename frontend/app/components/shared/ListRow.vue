<script setup lang="ts">
/**
 * ListRow — standard clickable row pattern.
 *
 * Visual anatomy:
 *   [leading] [title + subtitle] [spacer] [meta] [chevron if to]
 *
 * Slots:
 *   leading   — avatar, icon, etc.
 *   title     — main text
 *   subtitle  — secondary text
 *   meta      — right-side meta (badge, time, amount)
 *   actions   — right-side action icons
 */
interface Props {
  /** NuxtLink target — if provided, row becomes a link */
  to?: string
  /** If no `to`, row can still emit click */
  clickable?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  clickable: false
})

const emit = defineEmits<{
  click: [event: MouseEvent]
}>()

const isInteractive = computed(() => Boolean(props.to) || props.clickable)

function handleClick(e: MouseEvent) {
  if (props.clickable) emit('click', e)
}

const rowClass = computed(() => [
  'flex items-center gap-[var(--density-gap,0.75rem)] px-2 py-1 -mx-2 rounded-token-md transition-colors min-h-[var(--density-row-height,44px)]',
  isInteractive.value
    ? 'cursor-pointer hover:bg-surface-muted focus:bg-surface-muted focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]'
    : ''
])
</script>

<template>
  <NuxtLink
    v-if="to"
    :to="to"
    :class="rowClass"
  >
    <div
      v-if="$slots.leading"
      class="shrink-0"
    >
      <slot name="leading" />
    </div>
    <div class="flex-1 min-w-0">
      <div
        v-if="$slots.title"
        class="text-ui text-default truncate flex items-center gap-2 flex-wrap"
      >
        <slot name="title" />
      </div>
      <div
        v-if="$slots.subtitle"
        class="text-caption text-subtle truncate"
      >
        <slot name="subtitle" />
      </div>
    </div>
    <div
      v-if="$slots.meta"
      class="shrink-0 flex items-center gap-2"
    >
      <slot name="meta" />
    </div>
    <div
      v-if="$slots.actions"
      class="shrink-0 flex items-center gap-1"
    >
      <slot name="actions" />
    </div>
    <UIcon
      name="i-lucide-chevron-right"
      class="icon-density text-subtle shrink-0"
    />
  </NuxtLink>

  <div
    v-else
    :class="rowClass"
    :tabindex="clickable ? 0 : undefined"
    :role="clickable ? 'button' : undefined"
    @click="handleClick"
    @keydown.enter="clickable && handleClick($event as unknown as MouseEvent)"
    @keydown.space.prevent="clickable && handleClick($event as unknown as MouseEvent)"
  >
    <div
      v-if="$slots.leading"
      class="shrink-0"
    >
      <slot name="leading" />
    </div>
    <div class="flex-1 min-w-0">
      <div
        v-if="$slots.title"
        class="text-ui text-default truncate flex items-center gap-2 flex-wrap"
      >
        <slot name="title" />
      </div>
      <div
        v-if="$slots.subtitle"
        class="text-caption text-subtle truncate"
      >
        <slot name="subtitle" />
      </div>
    </div>
    <div
      v-if="$slots.meta"
      class="shrink-0 flex items-center gap-2"
    >
      <slot name="meta" />
    </div>
    <div
      v-if="$slots.actions"
      class="shrink-0 flex items-center gap-1"
    >
      <slot name="actions" />
    </div>
  </div>
</template>
