<script setup lang="ts">
const { resolve } = useModuleSlots()

const heroEntries = computed(() => resolve('dashboard.hero', {}))
const timelineEntries = computed(() => resolve('dashboard.timeline', {}))
const attentionEntries = computed(() => resolve('dashboard.attention', {}))
const activityEntries = computed(() => resolve('dashboard.activity', {}))
const widgetEntries = computed(() => resolve('dashboard.widgets', {}))

const hasAnyContent = computed(() =>
  heroEntries.value.length
  + timelineEntries.value.length
  + attentionEntries.value.length
  + activityEntries.value.length
  + widgetEntries.value.length > 0
)

const { t } = useI18n()
</script>

<template>
  <div class="space-y-8">
    <HomeGreeting />

    <section
      v-if="heroEntries.length > 0"
      class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
    >
      <ModuleSlot
        name="dashboard.hero"
        :ctx="{}"
      />
    </section>

    <section v-if="timelineEntries.length > 0">
      <ModuleSlot
        name="dashboard.timeline"
        :ctx="{}"
      />
    </section>

    <section
      v-if="attentionEntries.length > 0 || activityEntries.length > 0"
      class="grid grid-cols-1 lg:grid-cols-2 gap-6"
    >
      <div
        v-if="attentionEntries.length > 0"
        class="space-y-6"
      >
        <ModuleSlot
          name="dashboard.attention"
          :ctx="{}"
        />
      </div>
      <div
        v-if="activityEntries.length > 0"
        class="space-y-6"
        :class="{ 'lg:col-span-2': attentionEntries.length === 0 }"
      >
        <ModuleSlot
          name="dashboard.activity"
          :ctx="{}"
        />
      </div>
    </section>

    <section v-if="widgetEntries.length > 0">
      <ModuleSlot
        name="dashboard.widgets"
        :ctx="{}"
      />
    </section>

    <UCard v-if="!hasAnyContent">
      <EmptyState
        icon="i-lucide-smile"
        :title="t('dashboard.welcome')"
        :description="t('dashboard.welcomeMessage')"
      />
    </UCard>
  </div>
</template>
