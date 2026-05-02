<script setup lang="ts">
import type { Document } from '~~/app/types'

interface Props {
  open: boolean
  documents: Document[]
  startId?: string | null
}

const props = defineProps<Props>()
const emit = defineEmits<{ 'update:open': [boolean] }>()

const config = useRuntimeConfig()
const auth = useAuth()
const apiBaseUrl = computed(() =>
  import.meta.server ? config.apiBaseUrlServer : config.public.apiBaseUrl
)

const index = ref(0)

watch(
  () => [props.open, props.startId, props.documents.length] as const,
  () => {
    if (!props.open) return
    if (props.startId) {
      const i = props.documents.findIndex(d => d.id === props.startId)
      index.value = i >= 0 ? i : 0
    } else {
      index.value = 0
    }
  },
  { immediate: true }
)

const current = computed(() => props.documents[index.value] ?? null)

const blobUrl = ref<string | null>(null)

async function loadCurrent() {
  if (!current.value) return
  const path = current.value.medium_url ?? current.value.full_url
  if (!path) return
  try {
    const response = await $fetch<Blob>(path, {
      baseURL: apiBaseUrl.value,
      headers: { Authorization: `Bearer ${auth.accessToken.value}` },
      responseType: 'blob'
    })
    if (blobUrl.value) URL.revokeObjectURL(blobUrl.value)
    blobUrl.value = URL.createObjectURL(response)
  } catch {
    blobUrl.value = null
  }
}

// ``immediate`` so the first paint after a v-if mount loads the image —
// otherwise the watcher only fires on subsequent ids and the spinner
// stays forever (note attachments mount the lightbox on demand).
watch(() => current.value?.id, loadCurrent, { immediate: true })
onBeforeUnmount(() => {
  if (blobUrl.value) URL.revokeObjectURL(blobUrl.value)
})

function close() {
  emit('update:open', false)
}
function prev() {
  if (index.value > 0) index.value -= 1
}
function next() {
  if (index.value < props.documents.length - 1) index.value += 1
}

function onKey(e: KeyboardEvent) {
  if (!props.open) return
  if (e.key === 'ArrowLeft') prev()
  else if (e.key === 'ArrowRight') next()
  else if (e.key === 'Escape') close()
}

onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))

// Touch swipe
let touchStartX = 0
function onTouchStart(e: TouchEvent) {
  touchStartX = e.touches[0]?.clientX ?? 0
}
function onTouchEnd(e: TouchEvent) {
  const dx = (e.changedTouches[0]?.clientX ?? 0) - touchStartX
  if (Math.abs(dx) > 60) {
    if (dx > 0) prev()
    else next()
  }
}

const captureLabel = computed(() => {
  if (!current.value) return ''
  const ts = current.value.captured_at ?? current.value.created_at
  return ts ? new Date(ts).toLocaleString() : ''
})
</script>

<template>
  <UModal
    :open="props.open"
    fullscreen
    @update:open="emit('update:open', $event)"
  >
    <template #content>
      <div
        class="flex h-full w-full flex-col bg-black/95 text-white"
        @touchstart="onTouchStart"
        @touchend="onTouchEnd"
      >
        <!-- Top bar -->
        <div class="flex items-center justify-between gap-3 px-4 py-3 text-sm">
          <div class="flex flex-col">
            <span class="font-medium">{{ current?.title ?? '' }}</span>
            <span class="text-xs text-white/70">{{ captureLabel }}</span>
          </div>
          <div class="flex items-center gap-3">
            <span class="text-xs text-white/70">{{ index + 1 }} / {{ documents.length }}</span>
            <button
              type="button"
              class="flex h-9 w-9 items-center justify-center rounded-full bg-white/10 text-white hover:bg-white/20 focus:outline-none focus:ring-2 focus:ring-white/40"
              :aria-label="$t('actions.close', 'Cerrar')"
              @click="close"
            >
              <UIcon
                name="i-lucide-x"
                class="h-5 w-5"
              />
            </button>
          </div>
        </div>

        <!-- Image area -->
        <div class="relative flex flex-1 items-center justify-center overflow-hidden">
          <button
            v-if="index > 0"
            type="button"
            class="absolute left-2 top-1/2 hidden -translate-y-1/2 rounded-full bg-black/40 p-2 text-white hover:bg-black/60 sm:block"
            aria-label="Previous"
            @click="prev"
          >
            <UIcon
              name="i-lucide-chevron-left"
              class="h-6 w-6"
            />
          </button>
          <img
            v-if="blobUrl"
            :src="blobUrl"
            :alt="current?.title"
            class="max-h-full max-w-full select-none object-contain"
            draggable="false"
          >
          <div
            v-else
            class="text-white/70"
          >
            <UIcon
              name="i-lucide-loader-2"
              class="h-8 w-8 animate-spin"
            />
          </div>
          <button
            v-if="index < documents.length - 1"
            type="button"
            class="absolute right-2 top-1/2 hidden -translate-y-1/2 rounded-full bg-black/40 p-2 text-white hover:bg-black/60 sm:block"
            aria-label="Next"
            @click="next"
          >
            <UIcon
              name="i-lucide-chevron-right"
              class="h-6 w-6"
            />
          </button>
        </div>

        <!-- Metadata footer -->
        <div class="flex flex-wrap items-center justify-between gap-2 border-t border-white/10 px-4 py-2 text-xs">
          <div class="flex flex-wrap items-center gap-2">
            <UBadge
              v-if="current?.media_kind"
              color="neutral"
              variant="solid"
            >
              {{ current.media_kind }}
            </UBadge>
            <UBadge
              v-if="current?.media_category"
              color="primary"
              variant="soft"
            >
              {{ current.media_category }}
            </UBadge>
            <UBadge
              v-if="current?.media_subtype"
              color="primary"
              variant="outline"
            >
              {{ current.media_subtype }}
            </UBadge>
            <UBadge
              v-for="tag in current?.tags ?? []"
              :key="tag"
              color="neutral"
              variant="outline"
            >
              {{ tag }}
            </UBadge>
          </div>
        </div>
      </div>
    </template>
  </UModal>
</template>
