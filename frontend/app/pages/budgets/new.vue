<script setup lang="ts">
import type { Patient, BudgetCreate } from '~/types'

const router = useRouter()
const { t } = useI18n()
const toast = useToast()
const { can } = usePermissions()
const { createBudget } = useBudgets()

// Check permission
if (!can('budget.write')) {
  router.push('/budgets')
}

// Form state
const selectedPatient = ref<Patient | null>(null)
const isCreating = ref(false)

const form = reactive({
  valid_from: new Date().toISOString().split('T')[0],
  valid_until: '',
  patient_notes: '',
  internal_notes: ''
})

// Computed: can submit if patient is selected
const canSubmit = computed(() => !!selectedPatient.value && !isCreating.value)

async function handleCreate() {
  if (!selectedPatient.value) return

  isCreating.value = true

  try {
    const data: BudgetCreate = {
      patient_id: selectedPatient.value.id,
      valid_from: form.valid_from,
      valid_until: form.valid_until || undefined,
      patient_notes: form.patient_notes || undefined,
      internal_notes: form.internal_notes || undefined
    }

    const budget = await createBudget(data)

    toast.add({
      title: t('common.success'),
      description: t('budget.messages.created'),
      color: 'success'
    })

    // Navigate to the new budget to add items
    router.push(`/budgets/${budget.id}`)
  } catch {
    toast.add({
      title: t('common.error'),
      description: t('budget.errors.create'),
      color: 'error'
    })
  } finally {
    isCreating.value = false
  }
}
</script>

<template>
  <div class="max-w-2xl mx-auto space-y-6">
    <!-- Header -->
    <div class="flex items-center gap-4">
      <UButton
        variant="ghost"
        color="neutral"
        icon="i-lucide-arrow-left"
        @click="router.push('/budgets')"
      />
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        {{ t('budget.new') }}
      </h1>
    </div>

    <UCard>
      <form
        class="space-y-6"
        @submit.prevent="handleCreate"
      >
        <!-- Patient selection -->
        <UFormField
          :label="t('budget.patient')"
          required
        >
          <PatientSearch
            v-model="selectedPatient"
            :placeholder="t('budget.selectPatient')"
          />
          <p class="text-sm text-gray-500 mt-1">
            {{ t('budget.selectPatientHint') }}
          </p>
        </UFormField>

        <!-- Patient info card -->
        <div
          v-if="selectedPatient"
          class="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg"
        >
          <div class="flex items-center gap-3">
            <UAvatar
              :alt="selectedPatient.first_name"
              size="lg"
            />
            <div>
              <p class="font-medium text-gray-900 dark:text-white">
                {{ selectedPatient.last_name }}, {{ selectedPatient.first_name }}
              </p>
              <p class="text-sm text-gray-500">
                {{ selectedPatient.phone || selectedPatient.email || '-' }}
              </p>
            </div>
          </div>
        </div>

        <!-- Validity dates -->
        <div class="grid grid-cols-2 gap-4">
          <UFormField
            :label="t('budget.validFrom')"
            required
          >
            <UInput
              v-model="form.valid_from"
              type="date"
              required
            />
          </UFormField>
          <UFormField :label="t('budget.validUntil')">
            <UInput
              v-model="form.valid_until"
              type="date"
            />
            <p class="text-xs text-gray-500 mt-1">
              {{ t('budget.validUntilHint') }}
            </p>
          </UFormField>
        </div>

        <!-- Notes -->
        <UFormField :label="t('budget.patientNotes')">
          <UTextarea
            v-model="form.patient_notes"
            :placeholder="t('budget.patientNotesPlaceholder')"
            :rows="3"
          />
        </UFormField>

        <UFormField :label="t('budget.internalNotes')">
          <UTextarea
            v-model="form.internal_notes"
            :placeholder="t('budget.internalNotesPlaceholder')"
            :rows="3"
          />
        </UFormField>

        <!-- Actions -->
        <div class="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
          <UButton
            variant="outline"
            color="neutral"
            @click="router.push('/budgets')"
          >
            {{ t('common.cancel') }}
          </UButton>
          <UButton
            type="submit"
            color="primary"
            icon="i-lucide-plus"
            :disabled="!canSubmit"
            :loading="isCreating"
          >
            {{ t('budget.createAndAddItems') }}
          </UButton>
        </div>
      </form>
    </UCard>
  </div>
</template>
