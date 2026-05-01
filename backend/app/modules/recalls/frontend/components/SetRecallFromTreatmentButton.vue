<script setup lang="ts">
import { ref } from 'vue'
import type { RecallReason } from '../composables/useRecalls'

// Slot entry into `odontogram.condition.actions`. Ctx shape varies
// across hosts (treatment-plan rows, odontogram diagnosis list); we
// only read what's needed here and tolerate missing fields.
interface Props {
  patient?: { id: string }
  patientId?: string
  treatment?: {
    id?: string
    catalog_item?: { category?: { key?: string } } | null
  }
}
const props = defineProps<Props>()

const { t } = useI18n()
const open = ref(false)

const patientId = computed(() => props.patient?.id ?? props.patientId ?? null)
const treatmentId = computed(() => props.treatment?.id ?? null)
const treatmentCategoryKey = computed(
  () => props.treatment?.catalog_item?.category?.key ?? null
)

const reason = computed<RecallReason>(() => {
  // Keep in sync with backend `DEFAULT_CATEGORY_TO_REASON`.
  switch (treatmentCategoryKey.value) {
    case 'preventivo': return 'hygiene'
    case 'ortodoncia': return 'ortho_review'
    case 'cirugia': return 'post_op'
    case 'implantes': return 'implant_review'
    default: return 'treatment_followup'
  }
})

function onClick() {
  if (!patientId.value) return
  open.value = true
}
</script>

<template>
  <div v-if="patientId">
    <UButton
      icon="i-lucide-bell-plus"
      size="xs"
      color="neutral"
      variant="ghost"
      :title="t('recalls.setRecall')"
      @click="onClick"
    />
    <SetRecallModal
      v-model:open="open"
      :patient-id="patientId"
      :initial-reason="reason"
      :initial-treatment-id="treatmentId"
      :initial-treatment-category-key="treatmentCategoryKey"
    />
  </div>
</template>
