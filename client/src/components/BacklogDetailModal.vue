<template>
  <BaseModal :open="Boolean(isOpen && backlogItem)" :title="t('modals.backlog.title')" max-width="700px" @close="close">
    <div class="modal-body">
      <div class="shortage-header">
        <div class="shortage-icon">
          <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
            <path d="M24 8L24 28M24 34L24 36" stroke="currentColor" stroke-width="3" stroke-linecap="round" />
            <circle cx="24" cy="24" r="18" stroke="currentColor" stroke-width="3" />
          </svg>
        </div>
        <div class="shortage-title-section">
          <h4 class="item-name">{{ translateProductName(backlogItem.item_name) }}</h4>
          <div class="item-sku">{{ t('modals.sku', { sku: backlogItem.item_sku }) }}</div>
        </div>
        <span class="priority-badge" :class="backlogItem.priority">
          {{ t('modals.backlog.priorityBadge', { priority: translatePriority(backlogItem.priority) }) }}
        </span>
      </div>

      <div class="shortage-summary">
        <div class="summary-card danger">
          <div class="summary-label">{{ t('modals.backlog.shortageAmount') }}</div>
          <div class="summary-value">{{ t('modals.units', { n: shortage }) }}</div>
        </div>
        <div class="summary-card warning">
          <div class="summary-label">{{ t('modals.backlog.daysDelayed') }}</div>
          <div class="summary-value">{{ t('common.days', { n: backlogItem.days_delayed }) }}</div>
        </div>
      </div>

      <div class="info-grid">
        <div class="info-item">
          <div class="info-label">{{ t('modals.backlog.orderId') }}</div>
          <div class="info-value order-id">{{ backlogItem.order_id }}</div>
        </div>

        <div class="info-item">
          <div class="info-label">{{ t('modals.backlog.itemSku') }}</div>
          <div class="info-value sku">{{ backlogItem.item_sku }}</div>
        </div>

        <div class="info-item">
          <div class="info-label">{{ t('modals.backlog.quantityNeeded') }}</div>
          <div class="info-value">{{ t('modals.units', { n: backlogItem.quantity_needed }) }}</div>
        </div>

        <div class="info-item">
          <div class="info-label">{{ t('modals.backlog.quantityAvailable') }}</div>
          <div class="info-value">{{ t('modals.units', { n: backlogItem.quantity_available }) }}</div>
        </div>

        <div class="info-item">
          <div class="info-label">{{ t('modals.backlog.expectedDate') }}</div>
          <div class="info-value">{{ formatDate(backlogItem.expected_date) }}</div>
        </div>

        <div class="info-item">
          <div class="info-label">{{ t('modals.status') }}</div>
          <div class="info-value">
            <span class="badge danger">{{ t('status.backordered') }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="modal-footer">
      <button class="btn-secondary" @click="close">{{ t('common.close') }}</button>
    </div>
  </BaseModal>
</template>

<script setup>
import { computed } from 'vue'
import BaseModal from './BaseModal.vue'
import { useI18n } from '../composables/useI18n'

const { t, currentLocale, translateProductName } = useI18n()

const translatePriority = (priority) => {
  const key = String(priority || '').toLowerCase()
  return ['high', 'medium', 'low'].includes(key) ? t(`priority.${key}`) : priority
}

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false,
  },
  backlogItem: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['close'])

const shortage = computed(() => {
  if (!props.backlogItem) return 0
  return props.backlogItem.quantity_needed - props.backlogItem.quantity_available
})

const close = () => {
  emit('close')
}

const formatDate = (dateString) => {
  if (!dateString) return t('modals.na')
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return t('modals.na')
  return date.toLocaleDateString(currentLocale.value === 'ja' ? 'ja-JP' : 'en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}
</script>

<style scoped>
.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-8);
}

.shortage-header {
  display: flex;
  align-items: center;
  gap: var(--space-5);
  padding-bottom: var(--space-6);
  border-bottom: 1px solid var(--border);
  margin-bottom: var(--space-6);
}

.shortage-icon {
  width: 64px;
  height: 64px;
  background: var(--danger);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.shortage-title-section {
  flex: 1;
  min-width: 0;
}

.item-name {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--text);
  margin: 0 0 var(--space-2) 0;
}

.item-sku {
  font-size: var(--text-base);
  color: var(--text-muted);
  font-family: 'Monaco', 'Courier New', monospace;
}

.priority-badge {
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-md);
  font-size: var(--text-base);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  flex-shrink: 0;
}

.priority-badge.high {
  background: var(--danger-soft);
  color: var(--danger-ink);
}

.priority-badge.medium {
  background: var(--warning-soft);
  color: var(--warning-ink);
}

.priority-badge.low {
  background: var(--info-soft);
  color: var(--info-ink);
}

.shortage-summary {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-4);
  margin-bottom: var(--space-8);
}

.summary-card {
  padding: var(--space-5);
  border-radius: var(--radius-lg);
  border: 2px solid;
}

.summary-card.danger {
  border-color: var(--danger-border);
  background: var(--danger-soft);
}

.summary-card.warning {
  border-color: var(--warning-border);
  background: var(--warning-soft);
}

.summary-label {
  font-size: var(--text-sm);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  margin-bottom: var(--space-2);
}

.summary-value {
  font-size: var(--text-3xl);
  font-weight: 700;
  color: var(--text);
}

.summary-card.danger .summary-value {
  color: var(--danger);
}

.summary-card.warning .summary-value {
  color: var(--warning);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--space-6);
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.info-label {
  font-size: var(--text-sm);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
}

.info-value {
  font-size: var(--text-md);
  color: var(--text);
  font-weight: 500;
}

.info-value.order-id,
.info-value.sku {
  font-family: 'Monaco', 'Courier New', monospace;
  color: var(--info);
}

.modal-footer {
  padding: var(--space-6);
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
}

.btn-secondary {
  padding: var(--space-2) var(--space-5);
  background: var(--surface-muted);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  font-weight: 500;
  font-size: var(--text-base);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--duration) var(--ease);
  font-family: inherit;
}

.btn-secondary:hover {
  background: var(--border);
  border-color: var(--border-strong);
}
</style>
