<script setup lang="ts">
import { getPermission } from '~/config/permissions'

type Resource = 'patients' | 'appointments' | 'users'
type Action = 'read' | 'write'

interface Props {
  resource: Resource
  action: Action
  label?: string
  icon?: string
  color?: string
  variant?: 'solid' | 'outline' | 'soft' | 'ghost' | 'link'
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  disabled?: boolean
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  color: 'primary',
  variant: 'solid',
  size: 'sm',
  disabled: false,
  loading: false
})

const emit = defineEmits<{
  click: [event: MouseEvent]
}>()

const { can } = usePermissions()

// Get permission from centralized config
const requiredPermission = computed(() => getPermission(props.resource, props.action))

// Check if user has permission
const hasPermission = computed(() => can(requiredPermission.value))

// Only render if user has permission
const shouldRender = computed(() => hasPermission.value)

function handleClick(event: MouseEvent) {
  if (!props.disabled && !props.loading && hasPermission.value) {
    emit('click', event)
  }
}
</script>

<template>
  <UButton
    v-if="shouldRender"
    :icon="icon"
    :color="color"
    :variant="variant"
    :size="size"
    :disabled="disabled || loading"
    :loading="loading"
    @click="handleClick"
  >
    <slot>{{ label }}</slot>
  </UButton>
</template>
