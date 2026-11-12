<template>
  <BaseModal :open="Boolean(isOpen && product)" :title="t('modals.product.title')" max-width="700px" @close="close">
    <div class="modal-body">
      <div class="product-header">
        <div class="product-icon">
          <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
            <rect x="8" y="12" width="32" height="28" rx="2" stroke="currentColor" stroke-width="2.5" />
            <path d="M16 8V16M32 8V16M8 20H40" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" />
          </svg>
        </div>
        <div class="product-title-section">
          <h4 class="product-name">{{ product.name }}</h4>
          <div class="product-sku">{{ t('modals.sku', { sku: product.sku }) }}</div>
        </div>
        <span class="stock-badge" :class="getStockBadgeClass(product.stockLevel)">
          {{ translateStockLevel(product.stockLevel) }}
        </span>
      </div>

      <div class="info-grid">
        <div class="info-item">
          <div class="info-label">{{ t('modals.category') }}</div>
          <div class="info-value">{{ translateCategory(product.category) }}</div>
        </div>

        <div class="info-item">
          <div class="info-label">{{ t('modals.warehouse') }}</div>
          <div class="info-value">{{ translateWarehouse(product.warehouse) }}</div>
        </div>

        <div class="info-item">
          <div class="info-label">{{ t('modals.product.unitsOrdered') }}</div>
          <div class="info-value">{{ product.unitsOrdered }}</div>
        </div>

        <div class="info-item">
          <div class="info-label">{{ t('modals.product.totalRevenue') }}</div>
          <div class="info-value">{{ currencySymbol }}{{ product.revenue.toLocaleString() }}</div>
        </div>

        <div class="info-item">
          <div class="info-label">{{ t('modals.product.currentStock') }}</div>
          <div class="info-value">{{ t('modals.units', { n: product.quantityOnHand }) }}</div>
        </div>

        <div class="info-item">
          <div class="info-label">{{ t('modals.reorderPoint') }}</div>
          <div class="info-value">{{ t('modals.units', { n: product.reorderPoint }) }}</div>
        </div>

        <div class="info-item">
          <div class="info-label">{{ t('modals.product.firstOrderDate') }}</div>
          <div class="info-value">{{ formatDate(product.firstOrderDate) }}</div>
        </div>

        <div class="info-item">
          <div class="info-label">{{ t('modals.product.stockStatus') }}</div>
          <div class="info-value">
            <span :class="['badge', getStockBadgeClass(product.stockLevel)]">
              {{ translateStockLevel(product.stockLevel) }}
            </span>
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

const { t, currentCurrency, currentLocale, translateWarehouse } = useI18n()

const currencySymbol = computed(() => {
  return currentCurrency.value === 'JPY' ? '¥' : '$'
})

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false,
  },
  product: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['close'])

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

// Category / stock level strings come from the data in English; map known ones to translated labels
const translateCategory = (category) => {
  const keys = {
    'Circuit Boards': 'circuitBoards',
    Sensors: 'sensors',
    Actuators: 'actuators',
    Controllers: 'controllers',
    'Power Supplies': 'powerSupplies',
  }
  return keys[category] ? t(`categories.${keys[category]}`) : category
}

const translateStockLevel = (level) => {
  if (level === 'In Stock') return t('status.inStock')
  if (level === 'Low Stock') return t('status.lowStock')
  return level
}

const getStockBadgeClass = (stockLevel) => {
  if (stockLevel === 'In Stock') return 'success'
  if (stockLevel === 'Low Stock') return 'warning'
  if (stockLevel === 'Out of Stock') return 'danger'
  return 'info'
}
</script>

<style scoped>
.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-8);
}

.product-header {
  display: flex;
  align-items: center;
  gap: var(--space-5);
  padding-bottom: var(--space-6);
  border-bottom: 1px solid var(--border);
  margin-bottom: var(--space-8);
}

.product-icon {
  width: 64px;
  height: 64px;
  background: var(--info);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.product-title-section {
  flex: 1;
  min-width: 0;
}

.product-name {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--text);
  margin: 0 0 var(--space-2) 0;
}

.product-sku {
  font-size: var(--text-base);
  color: var(--text-muted);
  font-family: 'Monaco', 'Courier New', monospace;
}

.stock-badge {
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-md);
  font-size: var(--text-base);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  flex-shrink: 0;
}

.stock-badge.success {
  background: var(--success-soft);
  color: var(--success-ink);
}

.stock-badge.warning {
  background: var(--warning-soft);
  color: var(--warning-ink);
}

.stock-badge.danger {
  background: var(--danger-soft);
  color: var(--danger-ink);
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
