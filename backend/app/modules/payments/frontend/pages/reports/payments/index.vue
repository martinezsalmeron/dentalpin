<script setup lang="ts">
import type {
  PaymentsSummary,
  MethodBreakdown,
  ProfessionalBreakdown,
  AgingBuckets,
  RefundsReport
} from '~~/app/types'

definePageMeta({ middleware: 'auth' })

const { t } = useI18n()
const { summary, byMethod, byProfessional, aging, refunds } = usePaymentReports()

function defaultRange() {
  const to = new Date()
  const from = new Date()
  from.setMonth(from.getMonth() - 3)
  return { date_from: from.toISOString().slice(0, 10), date_to: to.toISOString().slice(0, 10) }
}

const range = ref(defaultRange())
const summaryData = ref<PaymentsSummary | null>(null)
const methodsData = ref<MethodBreakdown[]>([])
const profData = ref<ProfessionalBreakdown[]>([])
const agingData = ref<AgingBuckets | null>(null)
const refundsData = ref<RefundsReport | null>(null)
const loading = ref(false)

const currency = computed(() => summaryData.value?.currency || 'EUR')

const fmt = (n: number | string | undefined) =>
  new Intl.NumberFormat(undefined, { style: 'currency', currency: currency.value }).format(Number(n || 0))

async function refresh() {
  loading.value = true
  const [s, m, p, a, r] = await Promise.all([
    summary(range.value.date_from, range.value.date_to),
    byMethod(range.value.date_from, range.value.date_to),
    byProfessional(range.value.date_from, range.value.date_to),
    aging(),
    refunds(range.value.date_from, range.value.date_to)
  ])
  summaryData.value = s
  methodsData.value = m
  profData.value = p
  agingData.value = a
  refundsData.value = r
  loading.value = false
}

onMounted(() => { refresh() })
</script>

<template>
  <div class="space-y-6 p-4 md:p-6">
    <div class="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
      <h1 class="text-2xl font-semibold">{{ t('payments.reports.title') }}</h1>
      <div class="flex gap-2">
        <UInput v-model="range.date_from" type="date" />
        <UInput v-model="range.date_to" type="date" />
        <UButton icon="i-lucide-refresh-cw" @click="refresh">↻</UButton>
      </div>
    </div>

    <div v-if="summaryData" class="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
      <UCard>
        <div class="text-xs text-neutral-500">{{ t('payments.reports.collected') }}</div>
        <div class="text-xl font-semibold">{{ fmt(summaryData.total_collected) }}</div>
      </UCard>
      <UCard>
        <div class="text-xs text-neutral-500">{{ t('payments.reports.refunded') }}</div>
        <div class="text-xl font-semibold">{{ fmt(summaryData.total_refunded) }}</div>
      </UCard>
      <UCard>
        <div class="text-xs text-neutral-500">{{ t('payments.reports.net') }}</div>
        <div class="text-xl font-semibold">{{ fmt(summaryData.net_collected) }}</div>
      </UCard>
      <UCard>
        <div class="text-xs text-neutral-500">{{ t('payments.reports.patientCredit') }}</div>
        <div class="text-xl font-semibold">{{ fmt(summaryData.patient_credit_total) }}</div>
      </UCard>
      <UCard>
        <div class="text-xs text-neutral-500">{{ t('payments.reports.clinicReceivable') }}</div>
        <div class="text-xl font-semibold">{{ fmt(summaryData.clinic_receivable_total) }}</div>
      </UCard>
      <UCard>
        <div class="text-xs text-neutral-500">{{ t('payments.reports.refundRatio') }}</div>
        <div class="text-xl font-semibold">{{ (summaryData.refund_ratio * 100).toFixed(1) }}%</div>
      </UCard>
    </div>

    <UCard>
      <h2 class="mb-2 font-medium">{{ t('payments.reports.byMethod') }}</h2>
      <div v-if="methodsData.length === 0" class="text-sm text-neutral-500">—</div>
      <div v-else class="space-y-1">
        <div v-for="m in methodsData" :key="m.method" class="flex justify-between text-sm">
          <span>{{ t(`payments.methods.${m.method}`) }} · {{ m.count }}</span>
          <span class="font-medium">{{ fmt(m.total) }}</span>
        </div>
      </div>
    </UCard>

    <UCard>
      <h2 class="mb-2 font-medium">{{ t('payments.reports.byProfessional') }}</h2>
      <div v-if="profData.length === 0" class="text-sm text-neutral-500">—</div>
      <div v-else class="space-y-1">
        <div v-for="p in profData" :key="p.professional_id || 'unknown'" class="flex justify-between text-sm">
          <span>{{ p.professional_name || '—' }} · {{ p.count }}</span>
          <span class="font-medium">{{ fmt(p.total_earned) }}</span>
        </div>
      </div>
    </UCard>

    <UCard v-if="agingData">
      <h2 class="mb-2 font-medium">{{ t('payments.reports.aging') }}</h2>
      <div class="grid grid-cols-2 gap-2 md:grid-cols-4">
        <div v-for="b in agingData.buckets" :key="b.label" class="rounded border p-2 text-center">
          <div class="text-xs text-neutral-500">{{ b.label }} d</div>
          <div class="font-semibold">{{ fmt(b.total) }}</div>
          <div class="text-xs">{{ b.patient_count }} pacientes</div>
        </div>
      </div>
    </UCard>

    <UCard v-if="refundsData">
      <h2 class="mb-2 font-medium">{{ t('payments.reports.refunds') }}</h2>
      <div class="space-y-1 text-sm">
        <div v-for="r in refundsData.by_reason" :key="r.reason_code" class="flex justify-between">
          <span>{{ t(`payments.refund.reasonCodes.${r.reason_code}`) }} · {{ r.count }}</span>
          <span class="font-medium">{{ fmt(r.total) }}</span>
        </div>
      </div>
    </UCard>
  </div>
</template>
