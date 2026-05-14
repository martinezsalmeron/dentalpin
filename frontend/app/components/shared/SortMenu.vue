<script setup lang="ts">
/**
 * SortMenu — sort dropdown emitting canonical ``field:dir`` strings.
 *
 * The backend allow-list and the frontend menu items live in the same
 * page (the page declares which fields are sortable). Direction toggles
 * with a click on the current field, so this stays a single dropdown
 * instead of two controls.
 */
interface SortOption {
  /** Public field name — must match the backend allow-list. */
  field: string
  /** i18n-resolved label. */
  label: string
  /** Default direction for this field. */
  defaultDir?: 'asc' | 'desc'
}

interface Props {
  /** v-model: canonical ``field:dir`` string. */
  modelValue: string
  options: SortOption[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const { t } = useI18n()

const current = computed(() => {
  const [field, dir] = props.modelValue.split(':')
  return { field: field ?? '', dir: (dir as 'asc' | 'desc') ?? 'asc' }
})

const currentOption = computed(() =>
  props.options.find(o => o.field === current.value.field) ?? props.options[0]
)

function pick(opt: SortOption) {
  // If clicking the current field, toggle direction.
  if (opt.field === current.value.field) {
    const next = current.value.dir === 'asc' ? 'desc' : 'asc'
    emit('update:modelValue', `${opt.field}:${next}`)
    return
  }
  emit('update:modelValue', `${opt.field}:${opt.defaultDir ?? 'asc'}`)
}

function toggleDir() {
  const next = current.value.dir === 'asc' ? 'desc' : 'asc'
  emit('update:modelValue', `${current.value.field}:${next}`)
}

const items = computed(() => [
  props.options.map(opt => ({
    label: opt.label,
    icon: opt.field === current.value.field ? 'i-lucide-check' : undefined,
    onSelect: () => pick(opt)
  }))
])

const dirLabel = computed(() => t(`lists.sort.${current.value.dir}`))
</script>

<template>
  <div class="flex items-center gap-1">
    <UDropdownMenu :items="items">
      <UButton
        variant="outline"
        color="neutral"
        size="sm"
        icon="i-lucide-arrow-down-up"
        trailing-icon="i-lucide-chevron-down"
      >
        {{ currentOption?.label ?? t('lists.sort.label') }}
      </UButton>
    </UDropdownMenu>
    <UButton
      variant="ghost"
      color="neutral"
      size="sm"
      :icon="current.dir === 'asc' ? 'i-lucide-arrow-up' : 'i-lucide-arrow-down'"
      :aria-label="dirLabel"
      :title="dirLabel"
      @click="toggleDir"
    />
  </div>
</template>
