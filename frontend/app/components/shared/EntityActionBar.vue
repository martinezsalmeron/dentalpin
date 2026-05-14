<script setup lang="ts">
import type { DropdownMenuItem } from '@nuxt/ui'
import type { UiColor } from '~/config/severity'

export interface EntityAction {
  key: string
  label: string
  icon?: string
  color?: UiColor
  variant?: 'solid' | 'soft' | 'ghost' | 'outline' | 'subtle' | 'link'
  loading?: boolean
  disabled?: boolean
  destructive?: boolean
  onClick: () => void
}

interface Props {
  primary?: EntityAction[]
  overflow?: EntityAction[]
}

const props = withDefaults(defineProps<Props>(), {
  primary: () => [],
  overflow: () => []
})

const { t } = useI18n()
const { isMobile, isTablet } = useBreakpoint()

const visiblePrimaryCount = computed(() => {
  if (isMobile.value) return 1
  if (isTablet.value) return 2
  return 3
})

const visiblePrimary = computed(() => props.primary.slice(0, visiblePrimaryCount.value))
const collapsedPrimary = computed(() => props.primary.slice(visiblePrimaryCount.value))

const overflowItems = computed<DropdownMenuItem[][]>(() => {
  const collapsed = collapsedPrimary.value.map(toMenuItem)
  const extra = props.overflow.map(toMenuItem)
  const destructive = extra.filter(it => it.color === 'error')
  const nonDestructive = extra.filter(it => it.color !== 'error')

  const groups: DropdownMenuItem[][] = []
  const main = [...collapsed, ...nonDestructive]
  if (main.length) groups.push(main)
  if (destructive.length) groups.push(destructive)
  return groups
})

function toMenuItem(action: EntityAction): DropdownMenuItem {
  return {
    label: action.label,
    icon: action.icon,
    disabled: action.disabled,
    color: action.destructive ? 'error' : undefined,
    onSelect: () => action.onClick()
  }
}

const hasOverflow = computed(() => overflowItems.value.some(g => g.length > 0))
</script>

<template>
  <div class="flex flex-wrap items-center justify-end gap-2">
    <UButton
      v-for="action in visiblePrimary"
      :key="action.key"
      :color="action.color ?? 'primary'"
      :variant="action.variant ?? 'solid'"
      :icon="action.icon"
      :loading="action.loading"
      :disabled="action.disabled"
      size="sm"
      @click="action.onClick"
    >
      {{ action.label }}
    </UButton>

    <UDropdownMenu
      v-if="hasOverflow"
      :items="overflowItems"
    >
      <UButton
        variant="ghost"
        color="neutral"
        icon="i-lucide-more-horizontal"
        size="sm"
        :aria-label="t('shared.moreActions')"
      />
    </UDropdownMenu>
  </div>
</template>
