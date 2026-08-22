<script setup lang="ts">
// Toolbar filter chip on the invoice list ("invoice.list.toolbar.filters"
// slot). Reuses billing's generic `compliance_severity` filter — the
// same server-side mechanism verifactu's ComplianceFilter.vue uses —
// rather than a bespoke query param, so no billing change is needed
// beyond the slot mount point that already exists.

interface FilterCtx {
  severity?: string[]
  onChange?: (severities: string[]) => void
  clinic?: { country?: string | null, settings?: { country?: string | null } | null } | null
}

const props = defineProps<{ ctx: FilterCtx }>()
const { t } = useI18n()

const isActive = computed(() => (props.ctx.severity ?? []).includes('error') || (props.ctx.severity ?? []).includes('warning'))

function toggle() {
  const current = props.ctx.severity ?? []
  if (isActive.value) {
    props.ctx.onChange?.(current.filter(s => s !== 'error' && s !== 'warning'))
  } else {
    props.ctx.onChange?.([...new Set([...current, 'error', 'warning'])])
  }
}
</script>

<template>
  <UButton
    :variant="isActive ? 'solid' : 'outline'"
    :color="isActive ? 'warning' : 'neutral'"
    size="sm"
    icon="i-lucide-receipt-indian-rupee"
    @click="toggle"
  >
    {{ t('indiaGst.listFilter.needsAttention') }}
  </UButton>
</template>
