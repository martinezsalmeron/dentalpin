<script setup lang="ts">
import type { MultiToothTreatmentConfig, TreatmentStatus } from '~/types'

const props = defineProps<{
  open: boolean
  config: MultiToothTreatmentConfig
  teeth: number[]
  status: TreatmentStatus
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  'confirm': []
  'cancel': []
}>()

const { t } = useI18n()

const isBridge = computed(() => props.config.mode === 'bridge')

const sortedTeeth = computed(() => [...props.teeth].sort((a, b) => a - b))

const pillars = computed(() => {
  if (!isBridge.value || sortedTeeth.value.length < 2) return new Set<number>()
  const s = sortedTeeth.value
  return new Set<number>([s[0]!, s[s.length - 1]!])
})

const pontics = computed(() => {
  if (!isBridge.value) return new Set<number>()
  return new Set<number>(sortedTeeth.value.slice(1, -1))
})

function roleFor(tooth: number): 'pillar' | 'pontic' | null {
  if (pillars.value.has(tooth)) return 'pillar'
  if (pontics.value.has(tooth)) return 'pontic'
  return null
}

function handleCancel() {
  emit('cancel')
  emit('update:open', false)
}

function handleConfirm() {
  emit('confirm')
}
</script>

<template>
  <UModal
    :open="open"
    @update:open="emit('update:open', $event)"
  >
    <template #content>
      <div class="p-6 space-y-4 max-w-md">
        <h3 class="text-lg font-semibold">
          {{ t(config.labelKey) }}
        </h3>

        <p class="text-sm text-[var(--ui-text-muted)]">
          {{ t('odontogram.multiTooth.confirmHint', { n: teeth.length }) }}
        </p>

        <div class="flex flex-wrap gap-2">
          <UBadge
            v-for="tooth in sortedTeeth"
            :key="tooth"
            :color="roleFor(tooth) === 'pillar' ? 'primary' : 'neutral'"
            variant="subtle"
            size="lg"
          >
            {{ tooth }}
            <span
              v-if="roleFor(tooth)"
              class="ml-1 text-xs opacity-70"
            >
              ({{ t(`odontogram.multiTooth.${roleFor(tooth)}`) }})
            </span>
          </UBadge>
        </div>

        <div
          v-if="status === 'planned'"
          class="text-xs text-[var(--ui-text-muted)]"
        >
          {{ t('odontogram.multiTooth.willBePlanned') }}
        </div>
        <div
          v-else
          class="text-xs text-[var(--ui-text-muted)]"
        >
          {{ t('odontogram.multiTooth.willBeExisting') }}
        </div>

        <div class="flex justify-end gap-2 pt-2">
          <UButton
            variant="ghost"
            @click="handleCancel"
          >
            {{ t('common.cancel') }}
          </UButton>
          <UButton
            color="primary"
            @click="handleConfirm"
          >
            {{ t('common.confirm') }}
          </UButton>
        </div>
      </div>
    </template>
  </UModal>
</template>
