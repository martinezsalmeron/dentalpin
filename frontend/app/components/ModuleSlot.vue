<script setup lang="ts" generic="Ctx">
/**
 * Renders all components registered to the named slot, filtered by
 * permission + optional condition predicate, ordered by `order` asc.
 *
 * Each registered component receives the `ctx` prop verbatim.
 *
 * For ``settings.sections`` the slot supports ``categoryFilter``: when
 * set, only entries whose ``category`` matches (or, when ``categoryFilter``
 * is ``'modules'``, entries without a category — the fallback bucket)
 * render. Other slots ignore this prop.
 */

import { resolveSlot } from '~/composables/useModuleSlots'
import type { SettingsCategoryId } from '~/composables/useSettingsRegistry'

const props = defineProps<{
  name: string
  ctx: Ctx
  categoryFilter?: SettingsCategoryId
}>()

const { can } = usePermissions()

const entries = computed(() => {
  const all = resolveSlot<Ctx>(props.name, props.ctx, { can })
  if (!props.categoryFilter) return all
  const filter = props.categoryFilter
  return all.filter((entry) => {
    const cat = entry.category ?? 'modules'
    return cat === filter
  })
})
</script>

<template>
  <component
    :is="entry.component"
    v-for="entry in entries"
    :key="entry.id"
    :ctx="props.ctx"
  />
</template>
