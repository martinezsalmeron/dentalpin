<script setup lang="ts">
import { useData } from "vitepress";
import { computed } from "vue";

const { frontmatter, lang } = useData();

const isStale = computed(() => Boolean(frontmatter.value.staleSince));
const isSpanish = computed(() => lang.value.startsWith("es"));

const message = computed(() =>
  isSpanish.value
    ? "Esta página podría estar desactualizada"
    : "This page may be out of date",
);

const detail = computed(() => {
  const count = Number(frontmatter.value.staleCommits || 0);
  if (!count) return "";
  if (isSpanish.value) {
    return count === 1
      ? "1 commit nuevo desde la última verificación."
      : `${count} commits nuevos desde la última verificación.`;
  }
  return count === 1
    ? "1 new commit since last verification."
    : `${count} new commits since last verification.`;
});

const linkLabel = computed(() =>
  isSpanish.value ? "Ver cambios →" : "View changes →",
);
</script>

<template>
  <aside v-if="isStale" class="stale-badge" role="status">
    <div class="stale-badge__title">⚠ {{ message }}</div>
    <div v-if="detail" class="stale-badge__detail">{{ detail }}</div>
    <a
      v-if="frontmatter.staleDiffUrl"
      :href="frontmatter.staleDiffUrl"
      class="stale-badge__link"
      target="_blank"
      rel="noopener"
    >
      {{ linkLabel }}
    </a>
  </aside>
</template>

<style>
.stale-badge {
  margin: 0 0 1.5rem 0;
  padding: 0.85rem 1rem;
  border-radius: 8px;
  background: var(--vp-c-warning-soft, rgba(234, 179, 8, 0.12));
  border: 1px solid var(--vp-c-warning-2, rgba(234, 179, 8, 0.5));
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem 1rem;
  font-size: 0.92rem;
  line-height: 1.4;
}
.stale-badge__title {
  color: var(--vp-c-warning-1, #92651a);
  font-weight: 600;
}
.stale-badge__detail {
  color: var(--vp-c-text-2, #4b5563);
}
.stale-badge__link {
  color: var(--vp-c-warning-1, #92651a);
  text-decoration: underline;
  font-weight: 500;
  margin-left: auto;
}
.stale-badge__link:hover {
  text-decoration: none;
}
</style>
