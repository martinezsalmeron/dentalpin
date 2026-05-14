<script setup lang="ts">
/**
 * DataListItem — row wrapper with dual layout.
 *
 *   md+:    renders the ``row`` slot (compact horizontal row).
 *   <md:    renders the ``card`` slot (mobile-first card with prominent
 *           operational metric).
 *
 * Splits on ``NuxtLink`` vs ``div`` via ``v-if`` (same pattern as
 * ``ListRow``). Using ``<component :is="'NuxtLink'">`` proved unreliable
 * — string resolution didn't always pick up the global registration,
 * leaving rows non-clickable.
 */
interface Props {
  /** Optional NuxtLink target — when set, the whole row/card becomes a link. */
  to?: string
}

defineProps<Props>()

const wrapperClass
  = 'block focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary)] rounded-token-md'
const rowClass
  = 'hidden md:flex items-center gap-[var(--density-gap,0.75rem)] px-2 py-2 -mx-2 rounded-token-md transition-colors min-h-[var(--density-row-height,44px)] hover:bg-surface-muted'
const cardClass
  = 'md:hidden flex flex-col gap-2 px-3 py-3 -mx-3 rounded-token-md transition-colors min-h-[64px] hover:bg-surface-muted active:bg-surface-muted'
</script>

<template>
  <NuxtLink
    v-if="to"
    :to="to"
    :class="wrapperClass"
  >
    <div :class="rowClass">
      <slot name="row" />
    </div>
    <div :class="cardClass">
      <slot name="card">
        <slot name="row" />
      </slot>
    </div>
  </NuxtLink>

  <div
    v-else
    :class="wrapperClass"
  >
    <div :class="rowClass">
      <slot name="row" />
    </div>
    <div :class="cardClass">
      <slot name="card">
        <slot name="row" />
      </slot>
    </div>
  </div>
</template>
