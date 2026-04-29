<script setup lang="ts">
/**
 * Patient-facing budget view (ADR 0006). Mounted at
 * ``/p/budget/<token>`` and bypasses the global auth middleware
 * (see ``frontend/app/middleware/auth.global.ts``).
 *
 * State machine driven by the ``meta`` object the backend returns:
 *
 *   1. loading        → skeleton
 *   2. expired        → cold message + clinic phone
 *   3. locked         → cold message + clinic phone
 *   4. already decided→ confirmation screen ("ya aceptaste / rechazaste")
 *   5. requires_verification → BudgetVerifyForm
 *   6. ready          → budget detail + 3 CTAs (accept / doubts / reject)
 *
 * Acceptance and rejection submit to the cookie-protected endpoints
 * exposed by ``usePublicBudget``. The composable manages the cookie
 * via ``credentials: 'include'``.
 */

import BudgetVerifyForm from '../../../components/public/BudgetVerifyForm.vue'

definePageMeta({ layout: 'public' })

const route = useRoute()
const { t, locale } = useI18n()

const token = computed(() => route.params.token as string)

const {
  meta,
  budget,
  loading,
  verifying,
  submitting,
  lastError,
  decided,
  fetchMeta,
  fetchBudget,
  verify,
  accept,
  reject,
  requestChanges,
} = usePublicBudget(token.value)

onMounted(async () => {
  await fetchMeta()
  // If already decided or no verification needed, jump straight to the
  // detail (which will hydrate ``budget`` for the read-only confirmation
  // / ``method=none`` case).
  if (meta.value && !meta.value.requires_verification && !meta.value.locked && !meta.value.expired) {
    await fetchBudget()
  }
})

// ----- accept / reject / doubts modal state ----------------------------

const showAccept = ref(false)
const showReject = ref(false)
const showDoubts = ref(false)

const signerName = ref('')
const signaturePng = ref<string | null>(null)
const consentChecked = ref(false)

const rejectReason = ref<'price' | 'time' | 'second_opinion' | 'other'>('price')
const rejectNote = ref('')

const doubtsReason = ref<'price' | 'time' | 'second_opinion' | 'other'>('price')
const doubtsNote = ref('')

// ----- verify ---------------------------------------------------------

async function onVerifySubmit(payload: { method: string; value: string }) {
  const ok = await verify(payload.method as any, payload.value)
  if (ok) {
    await fetchMeta()
    await fetchBudget()
  }
}

// ----- accept ---------------------------------------------------------

const canvasRef = ref<HTMLCanvasElement | null>(null)
let drawing = false
let lastX = 0
let lastY = 0

function getCtx(): CanvasRenderingContext2D | null {
  return canvasRef.value?.getContext('2d') ?? null
}

function startDraw(ev: PointerEvent) {
  if (!canvasRef.value) return
  drawing = true
  const rect = canvasRef.value.getBoundingClientRect()
  lastX = ev.clientX - rect.left
  lastY = ev.clientY - rect.top
}

function moveDraw(ev: PointerEvent) {
  if (!drawing || !canvasRef.value) return
  const ctx = getCtx()
  if (!ctx) return
  const rect = canvasRef.value.getBoundingClientRect()
  const x = ev.clientX - rect.left
  const y = ev.clientY - rect.top
  ctx.strokeStyle = '#0f172a'
  ctx.lineWidth = 2
  ctx.lineCap = 'round'
  ctx.beginPath()
  ctx.moveTo(lastX, lastY)
  ctx.lineTo(x, y)
  ctx.stroke()
  lastX = x
  lastY = y
}

function endDraw() {
  if (!drawing || !canvasRef.value) return
  drawing = false
  signaturePng.value = canvasRef.value.toDataURL('image/png')
}

function clearSignature() {
  if (!canvasRef.value) return
  const ctx = getCtx()
  if (ctx) ctx.clearRect(0, 0, canvasRef.value.width, canvasRef.value.height)
  signaturePng.value = null
}

const canSubmitAccept = computed(
  () => signerName.value.trim().length > 0 && consentChecked.value
)

async function onAcceptSubmit() {
  if (!canSubmitAccept.value) return
  await accept({
    signer_name: signerName.value.trim(),
    signature_data: signaturePng.value ? { png: signaturePng.value } : undefined,
  })
  showAccept.value = false
}

// ----- reject / doubts -----------------------------------------------

async function onRejectSubmit() {
  await reject({
    reason: rejectReason.value,
    note: rejectNote.value.trim() || undefined,
  })
  showReject.value = false
}

async function onDoubtsSubmit() {
  await requestChanges({
    reason: doubtsReason.value,
    note: doubtsNote.value.trim() || undefined,
  })
  showDoubts.value = false
}

// ----- formatting -----------------------------------------------------

function formatMoney(amount: number, currency = 'EUR'): string {
  try {
    return new Intl.NumberFormat(locale.value, {
      style: 'currency',
      currency,
    }).format(amount)
  } catch {
    return `${amount.toFixed(2)} €`
  }
}

function formatDate(iso: string | null): string {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleDateString(locale.value, {
      day: '2-digit',
      month: 'long',
      year: 'numeric',
    })
  } catch {
    return iso
  }
}

const reasonOptions = computed(() => [
  { value: 'price', label: t('budget.public.reject.reasons.price') },
  { value: 'time', label: t('budget.public.reject.reasons.time') },
  { value: 'second_opinion', label: t('budget.public.reject.reasons.second_opinion') },
  { value: 'other', label: t('budget.public.reject.reasons.other') },
])
</script>

<template>
  <div class="max-w-3xl mx-auto px-4 py-6 space-y-4">
    <!-- Loading -->
    <div v-if="loading && !meta" class="space-y-3">
      <USkeleton class="h-12 w-2/3" />
      <USkeleton class="h-4 w-1/2" />
      <USkeleton class="h-64 w-full" />
    </div>

    <!-- Cold states -->
    <UAlert
      v-else-if="meta?.locked"
      color="error"
      variant="soft"
      icon="i-lucide-shield-alert"
      :description="t('budget.public.locked')"
    />
    <UAlert
      v-else-if="meta?.expired"
      color="warning"
      variant="soft"
      icon="i-lucide-clock-alert"
      :description="t('budget.public.expired')"
    />
    <UAlert
      v-else-if="meta?.already_decided && meta.decided_status === 'accepted'"
      color="success"
      variant="soft"
      icon="i-lucide-check-circle-2"
      :description="t('budget.public.already_accepted')"
    />
    <UAlert
      v-else-if="meta?.already_decided && meta.decided_status === 'rejected'"
      color="neutral"
      variant="soft"
      icon="i-lucide-info"
      :description="t('budget.public.already_rejected')"
    />

    <!-- Verify form -->
    <BudgetVerifyForm
      v-else-if="meta?.requires_verification"
      :method="meta.method"
      :verifying="verifying"
      :error="lastError"
      @submit="onVerifySubmit"
    />

    <!-- Budget view -->
    <template v-else-if="budget">
      <header class="space-y-1">
        <h1 class="text-2xl font-semibold">{{ t('budget.public.title') }}</h1>
        <p class="text-sm text-[var(--ui-text-muted)]">
          {{ t('budget.public.intro', { clinic: meta?.clinic_name || '' }) }}
        </p>
        <p v-if="budget.valid_until" class="text-xs text-[var(--ui-text-muted)]">
          {{ t('budget.public.validUntil', { date: formatDate(budget.valid_until) }) }}
        </p>
      </header>

      <UCard>
        <template #header>
          <h2 class="font-semibold">{{ t('budget.public.items') }}</h2>
        </template>

        <ul class="divide-y divide-[var(--ui-border)]">
          <li v-for="item in budget.items" :key="item.id" class="py-3 flex items-start justify-between gap-4">
            <div class="min-w-0">
              <p class="font-medium truncate">
                {{ item.catalog_item?.name || '—' }}
              </p>
              <p v-if="item.tooth_number" class="text-xs text-[var(--ui-text-muted)] mt-1">
                {{ t('budget.public.tooth', { number: item.tooth_number }) }}
              </p>
            </div>
            <div class="text-right text-sm shrink-0">
              <p>{{ item.quantity }} × {{ formatMoney(Number(item.unit_price), budget.currency) }}</p>
              <p class="font-semibold">{{ formatMoney(Number(item.line_total), budget.currency) }}</p>
            </div>
          </li>
        </ul>

        <template #footer>
          <dl class="space-y-1 text-sm">
            <div class="flex justify-between">
              <dt class="text-[var(--ui-text-muted)]">{{ t('budget.public.subtotal') }}</dt>
              <dd>{{ formatMoney(Number(budget.subtotal), budget.currency) }}</dd>
            </div>
            <div v-if="Number(budget.total_discount) > 0" class="flex justify-between">
              <dt class="text-[var(--ui-text-muted)]">{{ t('budget.public.discount') }}</dt>
              <dd>−{{ formatMoney(Number(budget.total_discount), budget.currency) }}</dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-[var(--ui-text-muted)]">{{ t('budget.public.tax') }}</dt>
              <dd>{{ formatMoney(Number(budget.total_tax), budget.currency) }}</dd>
            </div>
            <div class="flex justify-between text-lg font-bold pt-2 border-t border-[var(--ui-border)]">
              <dt>{{ t('budget.public.total') }}</dt>
              <dd>{{ formatMoney(Number(budget.total), budget.currency) }}</dd>
            </div>
          </dl>
        </template>
      </UCard>

      <!-- CTAs -->
      <div class="flex flex-col gap-3">
        <UButton color="primary" size="xl" block @click="showAccept = true">
          {{ t('budget.public.cta_accept') }}
        </UButton>
        <UButton color="neutral" variant="soft" size="lg" block @click="showDoubts = true">
          {{ t('budget.public.cta_doubts') }}
        </UButton>
        <UButton color="neutral" variant="ghost" size="sm" @click="showReject = true">
          {{ t('budget.public.cta_reject') }}
        </UButton>
      </div>
    </template>

    <!-- Accept modal -->
    <UModal v-model:open="showAccept">
      <template #content>
        <UCard>
          <template #header>
            <h3 class="text-lg font-semibold">{{ t('budget.public.accept.title') }}</h3>
          </template>

          <div class="space-y-4">
            <UFormField :label="t('budget.public.accept.signerLabel')" required>
              <UInput v-model="signerName" autofocus size="lg" />
            </UFormField>

            <div>
              <p class="text-sm text-[var(--ui-text-muted)] mb-2">
                {{ t('budget.public.accept.signatureLabel') }}
              </p>
              <div class="rounded-md border border-[var(--ui-border)] bg-white touch-none">
                <canvas
                  ref="canvasRef"
                  width="600"
                  height="180"
                  class="block w-full h-44 cursor-crosshair"
                  @pointerdown="startDraw"
                  @pointermove="moveDraw"
                  @pointerup="endDraw"
                  @pointerleave="endDraw"
                />
              </div>
              <UButton
                color="neutral"
                variant="ghost"
                size="xs"
                class="mt-2"
                @click="clearSignature"
              >
                {{ t('budget.public.accept.signatureClear') }}
              </UButton>
            </div>

            <UCheckbox v-model="consentChecked" :label="t('budget.public.accept.consent')" />
          </div>

          <template #footer>
            <div class="flex justify-end gap-2">
              <UButton color="neutral" variant="ghost" @click="showAccept = false">
                {{ t('common.cancel') }}
              </UButton>
              <UButton
                color="primary"
                :loading="submitting"
                :disabled="!canSubmitAccept"
                @click="onAcceptSubmit"
              >
                {{ t('budget.public.accept.submit') }}
              </UButton>
            </div>
          </template>
        </UCard>
      </template>
    </UModal>

    <!-- Reject modal -->
    <UModal v-model:open="showReject">
      <template #content>
        <UCard>
          <template #header>
            <h3 class="text-lg font-semibold">{{ t('budget.public.reject.title') }}</h3>
          </template>

          <div class="space-y-4">
            <p class="text-sm text-[var(--ui-text-muted)]">
              {{ t('budget.public.reject.intro') }}
            </p>
            <UFormField :label="t('budget.public.reject.reasonLabel')">
              <USelect v-model="rejectReason" :items="reasonOptions" class="w-full" />
            </UFormField>
            <UFormField :label="t('budget.public.reject.noteLabel')">
              <UTextarea v-model="rejectNote" :rows="3" :maxlength="2000" />
            </UFormField>
          </div>

          <template #footer>
            <div class="flex justify-end gap-2">
              <UButton color="neutral" variant="ghost" @click="showReject = false">
                {{ t('common.cancel') }}
              </UButton>
              <UButton color="error" :loading="submitting" @click="onRejectSubmit">
                {{ t('budget.public.reject.submit') }}
              </UButton>
            </div>
          </template>
        </UCard>
      </template>
    </UModal>

    <!-- Doubts modal -->
    <UModal v-model:open="showDoubts">
      <template #content>
        <UCard>
          <template #header>
            <h3 class="text-lg font-semibold">{{ t('budget.public.doubts.title') }}</h3>
          </template>

          <div class="space-y-4">
            <p class="text-sm text-[var(--ui-text-muted)]">
              {{ t('budget.public.doubts.intro') }}
            </p>
            <UFormField :label="t('budget.public.doubts.reasonLabel')">
              <USelect v-model="doubtsReason" :items="reasonOptions" class="w-full" />
            </UFormField>
            <UFormField :label="t('budget.public.doubts.noteLabel')">
              <UTextarea v-model="doubtsNote" :rows="3" :maxlength="2000" />
            </UFormField>
          </div>

          <template #footer>
            <div class="flex justify-end gap-2">
              <UButton color="neutral" variant="ghost" @click="showDoubts = false">
                {{ t('common.cancel') }}
              </UButton>
              <UButton color="primary" :loading="submitting" @click="onDoubtsSubmit">
                {{ t('budget.public.doubts.submit') }}
              </UButton>
            </div>
          </template>
        </UCard>
      </template>
    </UModal>
  </div>
</template>
