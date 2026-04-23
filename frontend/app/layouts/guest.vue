<script setup lang="ts">
</script>

<template>
  <div class="min-h-screen flex flex-col bg-canvas">
    <DemoBanner />
    <div class="flex-1 flex items-center justify-center">
      <slot />
    </div>
  </div>
</template>
