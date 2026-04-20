<script setup lang="ts">
/**
 * DiagnosisCTA - Contextual call-to-action for treatment plan creation
 *
 * Shows different CTAs based on draft plans state:
 * - No drafts:"Create Plan" button
 * - 1 draft:"Continue Plan {name}" button
 * - N drafts: Dropdown to select which plan to continue
 */

import type { TreatmentPlan } from '~~/app/types'

const props = defineProps<{
  draftPlans: TreatmentPlan[]
}>()

const emit = defineEmits<{
  create: []
  continue: [planId: string]
}>()

const { t } = useI18n()

const selectedDraftId = ref<string>('')

// Options for dropdown when multiple drafts exist
const draftOptions = computed(() =>
  props.draftPlans.map(plan => ({
    label: plan.title || t('treatmentPlans.untitledPlan'),
    value: plan.id
  }))
)

function handleContinue() {
  if (selectedDraftId.value) {
    emit('continue', selectedDraftId.value)
  }
}
</script>

<template>
  <UCard class="bg-[var(--color-primary-soft)] border-[var(--color-primary)]">
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
      <div class="flex items-center gap-2">
        <UIcon
          name="i-lucide-lightbulb"
          class="w-5 h-5 text-primary-accent"
        />
        <span class="font-medium">{{ t('clinical.diagnosis.readyToCreatePlan') }}</span>
      </div>

      <!-- No drafts: Create new plan -->
      <UButton
        v-if="draftPlans.length === 0"
        color="primary"
        icon="i-lucide-plus"
        @click="emit('create')"
      >
        {{ t('clinical.diagnosis.createPlan') }}
      </UButton>

      <!-- 1 draft: Continue that plan -->
      <UButton
        v-else-if="draftPlans.length === 1"
        color="primary"
        icon="i-lucide-arrow-right"
        @click="emit('continue', draftPlans[0].id)"
      >
        {{ t('clinical.diagnosis.continuePlan', { name: draftPlans[0].title || t('treatmentPlans.untitledPlan') }) }}
      </UButton>

      <!-- N drafts: Dropdown to select -->
      <div
        v-else
        class="flex items-center gap-2"
      >
        <USelectMenu
          v-model="selectedDraftId"
          :options="draftOptions"
          option-attribute="label"
          value-attribute="value"
          :placeholder="t('clinical.diagnosis.selectPlan')"
          class="w-48"
        />
        <UButton
          color="primary"
          icon="i-lucide-arrow-right"
          :disabled="!selectedDraftId"
          @click="handleContinue"
        >
          {{ t('clinical.diagnosis.continue') }}
        </UButton>
      </div>
    </div>
  </UCard>
</template>
