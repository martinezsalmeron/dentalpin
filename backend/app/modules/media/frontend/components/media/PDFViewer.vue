<script setup lang="ts">
interface Props {
  blobUrl: string
}

defineProps<Props>()
</script>

<template>
  <iframe
    :src="blobUrl"
    class="w-full h-full border-0"
    type="application/pdf"
  />
</template>
