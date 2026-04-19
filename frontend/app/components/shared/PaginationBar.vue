<script setup lang="ts">
interface Props {
  page: number
  totalPages: number
  total?: number
  pageSize?: number
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:page': [value: number]
}>()

const { t } = useI18n()

const canPrev = computed(() => props.page > 1)
const canNext = computed(() => props.page < props.totalPages)

function prev() {
  if (canPrev.value) emit('update:page', props.page - 1)
}
function next() {
  if (canNext.value) emit('update:page', props.page + 1)
}
</script>

<template>
  <div
    v-if="totalPages > 1"
    class="flex items-center justify-between pt-4 mt-4 border-t border-subtle"
  >
    <span class="text-caption text-subtle tnum">
      {{ t('common.page', { current: page, total: totalPages }) }}
    </span>
    <div class="flex gap-2">
      <UButton
        variant="outline"
        color="neutral"
        size="sm"
        :disabled="!canPrev"
        icon="i-lucide-chevron-left"
        :aria-label="t('common.previous')"
        @click="prev"
      >
        <span class="hidden sm:inline">{{ t('common.previous') }}</span>
      </UButton>
      <UButton
        variant="outline"
        color="neutral"
        size="sm"
        :disabled="!canNext"
        trailing-icon="i-lucide-chevron-right"
        :aria-label="t('common.next')"
        @click="next"
      >
        <span class="hidden sm:inline">{{ t('common.next') }}</span>
      </UButton>
    </div>
  </div>
</template>
