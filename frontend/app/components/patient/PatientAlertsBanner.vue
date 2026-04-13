<script setup lang="ts">
import type { PatientAlert } from '~/types'

interface Props {
  alerts: PatientAlert[]
  compact?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  compact: false
})

const { t } = useI18n()

// Get icon for alert type
function getAlertIcon(type: PatientAlert['type']): string {
  const icons: Record<PatientAlert['type'], string> = {
    allergy: 'i-lucide-alert-triangle',
    pregnancy: 'i-lucide-baby',
    lactating: 'i-lucide-heart',
    anticoagulant: 'i-lucide-droplet',
    anesthesia_reaction: 'i-lucide-syringe',
    systemic_disease: 'i-lucide-activity'
  }
  return icons[type] || 'i-lucide-alert-circle'
}

// Get color for severity
function getSeverityColor(severity: PatientAlert['severity']): string {
  const colors: Record<PatientAlert['severity'], string> = {
    critical: 'error',
    high: 'warning',
    medium: 'info',
    low: 'neutral'
  }
  return colors[severity] || 'neutral'
}

const criticalAlerts = computed(() =>
  props.alerts.filter(a => a.severity === 'critical' || a.severity === 'high')
)

const showExpanded = ref(false)
</script>

<template>
  <div
    v-if="alerts.length > 0"
    class="patient-alerts-banner"
  >
    <!-- Compact mode: just badges -->
    <div
      v-if="compact"
      class="flex flex-wrap gap-1"
    >
      <UBadge
        v-for="(alert, index) in alerts"
        :key="index"
        :color="getSeverityColor(alert.severity)"
        size="xs"
        variant="subtle"
      >
        <UIcon
          :name="getAlertIcon(alert.type)"
          class="w-3 h-3 mr-1"
        />
        {{ alert.title }}
      </UBadge>
    </div>

    <!-- Full mode: expandable card -->
    <UCard
      v-else
      class="border-l-4"
      :class="criticalAlerts.length > 0 ? 'border-l-error-500' : 'border-l-warning-500'"
    >
      <div class="flex items-start justify-between">
        <div class="flex items-center gap-2">
          <UIcon
            :name="criticalAlerts.length > 0 ? 'i-lucide-alert-octagon' : 'i-lucide-alert-triangle'"
            :class="criticalAlerts.length > 0 ? 'text-error-500' : 'text-warning-500'"
            class="w-5 h-5"
          />
          <span class="font-medium">
            {{ t('patients.alerts.title', { count: alerts.length }) }}
          </span>
        </div>
        <UButton
          v-if="alerts.length > 2"
          variant="ghost"
          size="xs"
          :icon="showExpanded ? 'i-lucide-chevron-up' : 'i-lucide-chevron-down'"
          @click="showExpanded = !showExpanded"
        />
      </div>

      <div class="mt-2 flex flex-wrap gap-2">
        <template
          v-for="(alert, index) in (showExpanded ? alerts : alerts.slice(0, 3))"
          :key="index"
        >
          <UTooltip
            v-if="alert.details"
            :text="alert.details"
          >
            <UBadge
              :color="getSeverityColor(alert.severity)"
              size="sm"
              variant="subtle"
            >
              <UIcon
                :name="getAlertIcon(alert.type)"
                class="w-4 h-4 mr-1"
              />
              {{ alert.title }}
            </UBadge>
          </UTooltip>
          <UBadge
            v-else
            :color="getSeverityColor(alert.severity)"
            size="sm"
            variant="subtle"
          >
            <UIcon
              :name="getAlertIcon(alert.type)"
              class="w-4 h-4 mr-1"
            />
            {{ alert.title }}
          </UBadge>
        </template>
        <span
          v-if="!showExpanded && alerts.length > 3"
          class="text-sm text-gray-500"
        >
          +{{ alerts.length - 3 }} {{ t('common.more') }}
        </span>
      </div>
    </UCard>
  </div>
</template>

<style scoped>
.patient-alerts-banner {
  width: 100%;
}
</style>
