<script setup lang="ts">
import type { Recall } from '../composables/useRecalls'

interface Props {
  items: Recall[]
  isLoading: boolean
}
defineProps<Props>()

const emit = defineEmits<{ changed: [recall: Recall] }>()
const { t } = useI18n()
</script>

<template>
  <div>
    <USkeleton
      v-if="isLoading"
      class="h-32 w-full"
    />
    <div
      v-else-if="items.length === 0"
      class="rounded-token-md border border-default bg-default p-6 text-center text-subtle"
    >
      {{ t('recalls.noRecallsThisMonth') }}
    </div>
    <ul
      v-else
      class="space-y-2"
    >
      <li
        v-for="recall in items"
        :key="recall.id"
      >
        <RecallRow
          :recall="recall"
          @changed="emit('changed', $event)"
        />
      </li>
    </ul>
  </div>
</template>
