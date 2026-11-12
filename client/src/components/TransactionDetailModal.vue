<template>
  <BaseModal
    :open="Boolean(isOpen && transaction)"
    :title="t('modals.transaction.title')"
    max-width="520px"
    @close="close"
  >
    <div class="modal-body">
      <!-- Definition list: label/value pairs for every field the transaction carries -->
      <dl class="detail-list">
        <div v-for="row in rows" :key="row.key" class="detail-row">
          <dt class="detail-label">{{ row.label }}</dt>
          <dd class="detail-value" :class="{ amount: row.key === 'amount' }">{{ row.value }}</dd>
        </div>
      </dl>
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

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  transaction: { type: Object, default: null },
})

const emit = defineEmits(['close'])

const { t, currentCurrency, currentLocale } = useI18n()

// Same presentation as the transactions table (symbol + amount, no FX conversion)
const currencySymbol = computed(() => (currentCurrency.value === 'JPY' ? '¥' : '$'))

const close = () => emit('close')

const formatDate = (value) => {
  const date = new Date(value)
  if (!value || isNaN(date.getTime())) return t('modals.na')
  return date.toLocaleDateString(currentLocale.value === 'ja' ? 'ja-JP' : 'en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

// Only fields present on the transaction are shown (optional ones are skipped when empty)
const rows = computed(() => {
  const tx = props.transaction
  if (!tx) return []
  const candidates = [
    { key: 'id', label: t('modals.transaction.id'), value: tx.id },
    { key: 'description', label: t('modals.transaction.description'), value: tx.description },
    { key: 'vendor', label: t('modals.transaction.vendor'), value: tx.vendor },
    { key: 'date', label: t('modals.transaction.date'), value: tx.date ? formatDate(tx.date) : '' },
    { key: 'category', label: t('modals.transaction.category'), value: tx.category },
    { key: 'type', label: t('modals.transaction.type'), value: tx.type },
    { key: 'warehouse', label: t('modals.transaction.warehouse'), value: tx.warehouse },
    {
      key: 'amount',
      label: t('modals.transaction.amount'),
      value: typeof tx.amount === 'number' ? `${currencySymbol.value}${tx.amount.toLocaleString()}` : '',
    },
  ]
  return candidates.filter((row) => row.value !== undefined && row.value !== null && row.value !== '')
})
</script>

<style scoped>
.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-6) var(--space-8);
}

.detail-list {
  display: flex;
  flex-direction: column;
}

.detail-row {
  display: grid;
  grid-template-columns: 120px 1fr;
  gap: var(--space-4);
  padding: var(--space-3) 0;
  border-bottom: 1px solid var(--border);
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-label {
  font-size: var(--text-sm);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
}

.detail-value {
  font-size: var(--text-base);
  color: var(--text);
  overflow-wrap: anywhere;
}

.detail-value.amount {
  font-weight: 700;
}

.modal-footer {
  padding: var(--space-6);
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: flex-end;
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
