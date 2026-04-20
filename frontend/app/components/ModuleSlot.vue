<script setup lang="ts" generic="Ctx">
/**
 * Renders all components registered to the named slot, filtered by
 * permission + optional condition predicate, ordered by `order` asc.
 *
 * Each registered component receives the `ctx` prop verbatim.
 */

import { resolveSlot } from '~/composables/useModuleSlots'

const props = defineProps<{
  name: string
  ctx: Ctx
}>()

const { can } = usePermissions()

const entries = computed(() =>
  resolveSlot<Ctx>(props.name, props.ctx, { can })
)
</script>

<template>
  <component
    :is="entry.component"
    v-for="entry in entries"
    :key="entry.id"
    :ctx="props.ctx"
  />
</template>
