<script setup>
// Client-side pager. Controlled via v-model:page (1-based). Renders nothing when everything fits on one page.
import { computed } from 'vue'
import { useI18n } from '../composables/useI18n'

const props = defineProps({
  pageSize: { type: Number, required: true },
  total: { type: Number, required: true },
})

const page = defineModel('page', { type: Number, default: 1 })
const { t } = useI18n()

const pageCount = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))
// Clamp for display so a stale page never renders a nonsensical range
const current = computed(() => Math.min(Math.max(page.value, 1), pageCount.value))
const rangeStart = computed(() => (props.total === 0 ? 0 : (current.value - 1) * props.pageSize + 1))
const rangeEnd = computed(() => Math.min(current.value * props.pageSize, props.total))

// Always show first, last and current +/- 1; gaps become an ellipsis entry.
// A gap of exactly one page is rendered as that page (an ellipsis would hide nothing extra).
const items = computed(() => {
  const last = pageCount.value
  const wanted = new Set([1, last, current.value - 1, current.value, current.value + 1])
  const pages = [...wanted].filter((p) => p >= 1 && p <= last).sort((a, b) => a - b)
  const out = []
  for (let i = 0; i < pages.length; i++) {
    const p = pages[i]
    const prev = pages[i - 1]
    if (prev !== undefined && p - prev === 2) out.push({ key: `p${prev + 1}`, page: prev + 1 })
    else if (prev !== undefined && p - prev > 2) out.push({ key: `gap-${prev}`, gap: true })
    out.push({ key: `p${p}`, page: p })
  }
  return out
})

const go = (p) => {
  const next = Math.min(Math.max(p, 1), pageCount.value)
  if (next !== page.value) page.value = next
}
</script>

<template>
  <nav v-if="total > pageSize" class="pagination" :aria-label="t('pagination.label')">
    <p class="pagination-summary" aria-live="polite">
      {{ t('pagination.showing', { start: rangeStart, end: rangeEnd, total }) }}
    </p>
    <div class="pagination-controls">
      <button
        type="button"
        class="page-btn page-btn--nav"
        :disabled="current <= 1"
        :aria-label="t('pagination.previousPage')"
        @click="go(current - 1)"
      >
        {{ t('pagination.previous') }}
      </button>
      <template v-for="item in items" :key="item.key">
        <span v-if="item.gap" class="page-gap" aria-hidden="true">&hellip;</span>
        <button
          v-else
          type="button"
          :class="['page-btn', { active: item.page === current }]"
          :aria-label="t('pagination.page', { n: item.page })"
          :aria-current="item.page === current ? 'page' : undefined"
          @click="go(item.page)"
        >
          {{ item.page }}
        </button>
      </template>
      <button
        type="button"
        class="page-btn page-btn--nav"
        :disabled="current >= pageCount"
        :aria-label="t('pagination.nextPage')"
        @click="go(current + 1)"
      >
        {{ t('pagination.next') }}
      </button>
    </div>
  </nav>
</template>

<style scoped>
.pagination {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  margin-top: var(--space-4);
  padding-top: var(--space-4);
  border-top: 1px solid var(--border);
}

.pagination-summary {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--text-muted);
}

/* Wraps instead of overflowing on narrow viewports */
.pagination-controls {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-1);
}

.page-btn {
  min-width: 36px;
  height: 36px;
  padding: 0 var(--space-3);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-md);
  background: var(--surface);
  color: var(--text);
  font-size: var(--text-base);
  cursor: pointer;
  transition: background var(--duration) var(--ease);
}

.page-btn:hover:not(:disabled):not(.active) {
  background: var(--surface-muted);
}

.page-btn:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

.page-btn.active {
  background: var(--accent);
  border-color: var(--accent);
  color: var(--accent-ink);
  font-weight: 600;
  cursor: default;
}

.page-btn:disabled {
  color: var(--text-subtle);
  background: var(--surface-subtle);
  cursor: not-allowed;
}

.page-gap {
  min-width: 24px;
  text-align: center;
  color: var(--text-muted);
}
</style>
