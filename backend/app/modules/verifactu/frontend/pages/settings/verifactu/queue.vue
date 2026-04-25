<script setup lang="ts">
const { t } = useI18n()
const { listQueue, retryRecord, processNow } = useVerifactu()
const { can } = usePermissions()
const toast = useToast?.()

const tab = ref<'pending' | 'rejected' | 'failed_transient'>('pending')
const items = ref<Awaited<ReturnType<typeof listQueue>>>([])
const loading = ref(false)
const processing = ref(false)

async function refresh() {
  loading.value = true
  try {
    items.value = await listQueue(tab.value)
  } finally {
    loading.value = false
  }
}

async function retry(id: string) {
  await retryRecord(id)
  await refresh()
}

async function process() {
  processing.value = true
  try {
    const r = await processNow()
    toast?.add({ title: t('verifactu.queue.processed', { n: r.processed }), color: 'green' })
    await refresh()
  } finally {
    processing.value = false
  }
}

watch(tab, refresh)
onMounted(refresh)
</script>

<template>
  <div class="p-4 sm:p-6 max-w-4xl mx-auto space-y-4">
    <header class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <NuxtLink to="/settings/verifactu" class="text-sm text-gray-500">← Verifactu</NuxtLink>
        <h1 class="text-2xl font-semibold mt-2">{{ t('verifactu.queue.title') }}</h1>
      </div>
      <UButton v-if="can('verifactu.queue.manage')" :loading="processing" variant="soft" @click="process">
        {{ t('verifactu.queue.processNow') }}
      </UButton>
    </header>

    <div class="flex gap-2 border-b">
      <button
        v-for="t_ in (['pending','rejected','failed_transient'] as const)"
        :key="t_"
        class="px-3 py-2 text-sm border-b-2"
        :class="tab === t_ ? 'border-primary text-primary' : 'border-transparent text-gray-500'"
        @click="tab = t_"
      >
        {{ t(`verifactu.queue.tabs.${t_ === 'failed_transient' ? 'transient' : t_}`) }}
      </button>
    </div>

    <div v-if="loading" class="space-y-2">
      <USkeleton class="h-16 w-full" v-for="i in 3" :key="i" />
    </div>
    <p v-else-if="items.length === 0" class="text-sm text-gray-500">{{ t('verifactu.queue.empty') }}</p>
    <ul v-else class="divide-y">
      <li v-for="item in items" :key="item.id" class="py-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div class="text-sm min-w-0 flex-1">
          <div class="font-medium">{{ item.serie_numero }} · {{ item.importe_total }}€</div>
          <div
            v-if="item.aeat_descripcion_error"
            class="text-red-600 break-words mt-1"
          >
            <span v-if="item.aeat_codigo_error && item.aeat_codigo_error > 0">
              {{ t('verifactu.queue.errorCode') }} {{ item.aeat_codigo_error }}:
            </span>
            <span v-else-if="item.aeat_codigo_error === -1">
              {{ t('verifactu.queue.transportError') }}:
            </span>
            <span v-else-if="item.aeat_codigo_error === -2">
              {{ t('verifactu.queue.aeatFault') }}:
            </span>
            {{ item.aeat_descripcion_error }}
          </div>
          <div class="text-gray-500 mt-1">{{ t('verifactu.queue.submissionAttempt', { n: item.submission_attempt }) }}</div>
        </div>
        <div class="flex flex-wrap gap-2">
          <UButton :to="`/invoices/${item.invoice_id}`" variant="soft" size="sm">
            {{ t('verifactu.queue.viewInvoice') }}
          </UButton>
          <UButton
            v-if="can('verifactu.queue.manage') && item.state === 'rejected'"
            color="primary"
            size="sm"
            @click="retry(item.id)"
          >
            {{ t('verifactu.queue.retry') }}
          </UButton>
        </div>
      </li>
    </ul>
  </div>
</template>
