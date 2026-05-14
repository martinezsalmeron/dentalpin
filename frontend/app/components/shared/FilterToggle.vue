<script setup lang="ts">
/**
 * FilterToggle — boolean / tri-state chip.
 *
 * When ``tristate`` is true, the model cycles:
 *   null  →  true  →  false  →  null
 * Used by /patients ``do_not_contact`` (todos / sólo no contactar /
 * sólo contactables). Otherwise it's a plain on/off.
 */
interface Props {
  label: string
  modelValue: boolean | null
  icon?: string
  tristate?: boolean
  /** Optional separate label for the "false" state in tri-state mode. */
  labelFalse?: string
}

const props = withDefaults(defineProps<Props>(), {
  icon: undefined,
  tristate: false,
  labelFalse: undefined
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean | null]
}>()

function cycle() {
  if (!props.tristate) {
    emit('update:modelValue', !props.modelValue)
    return
  }
  if (props.modelValue === null) emit('update:modelValue', true)
  else if (props.modelValue === true) emit('update:modelValue', false)
  else emit('update:modelValue', null)
}

const isActive = computed(() => props.modelValue !== null && props.modelValue !== false)

const displayLabel = computed(() => {
  if (!props.tristate) return props.label
  if (props.modelValue === false && props.labelFalse) return props.labelFalse
  return props.label
})

const displayIcon = computed(() => {
  if (props.tristate && props.modelValue === false) return 'i-lucide-x'
  if (isActive.value) return 'i-lucide-check'
  return props.icon
})
</script>

<template>
  <UButton
    :color="isActive ? 'primary' : 'neutral'"
    :variant="isActive ? 'soft' : 'outline'"
    size="sm"
    :icon="displayIcon"
    @click="cycle"
  >
    {{ displayLabel }}
  </UButton>
</template>
