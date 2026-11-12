<template>
  <BaseModal
    :open="Boolean(isOpen && inventoryItem)"
    :title="t('modals.inventory.title')"
    max-width="700px"
    @close="close"
  >
    <div class="modal-body">
      <div class="item-header">
        <div class="item-icon" :class="getStockIconClass()">
          <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
            <rect x="8" y="12" width="32" height="28" rx="2" stroke="currentColor" stroke-width="2.5" />
            <path d="M16 8V16M32 8V16M8 20H40" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" />
            <path d="M16 28H32M16 34H24" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" />
          </svg>
        </div>
        <div class="item-title-section">
          <h4 class="item-name">{{ translateProductName(inventoryItem.name) }}</h4>
          <div class="item-sku">{{ t('modals.sku', { sku: inventoryItem.sku }) }}</div>
        </div>
        <span class="stock-badge" :class="getStockStatusClass()">
          {{ getStockStatus() }}
        </span>
      </div>

      <div class="stock-summary">
        <div class="summary-card primary">
          <div class="summary-label">{{ t('modals.inventory.quantityOnHand') }}</div>
          <div class="summary-value">{{ t('modals.units', { n: inventoryItem.quantity_on_hand }) }}</div>
        </div>
        <div class="summary-card" :class="getSummaryCardClass()">
          <div class="summary-label">{{ t('modals.inventory.stockLevel') }}</div>
          <div class="summary-value">{{ stockPercentage }}%</div>
          <div class="summary-subtitle">{{ t('modals.inventory.vsReorder') }}</div>
        </div>
      </div>

      <div class="info-grid">
        <div class="info-item">
          <div class="info-label">{{ t('modals.category') }}</div>
          <div class="info-value">{{ translateCategory(inventoryItem.category) }}</div>
        </div>

        <div class="info-item">
          <div class="info-label">{{ t('modals.inventory.location') }}</div>
          <div class="info-value">{{ translateWarehouse(inventoryItem.location) }}</div>
        </div>

        <div class="info-item">
          <div class="info-label">{{ t('modals.reorderPoint') }}</div>
          <div class="info-value">{{ t('modals.units', { n: inventoryItem.reorder_point }) }}</div>
        </div>

        <div class="info-item">
          <div class="info-label">{{ t('modals.inventory.unitsRemaining') }}</div>
          <div class="info-value">
            <span
              :style="{
                color:
                  inventoryItem.quantity_on_hand <= inventoryItem.reorder_point ? 'var(--danger)' : 'var(--success)',
              }"
            >
              {{ t('modals.units', { n: inventoryItem.quantity_on_hand - inventoryItem.reorder_point }) }}
            </span>
          </div>
        </div>

        <div class="info-item">
          <div class="info-label">{{ t('modals.inventory.unitCost') }}</div>
          <div class="info-value">{{ currencySymbol }}{{ inventoryItem.unit_cost.toFixed(2) }}</div>
        </div>

        <div class="info-item">
          <div class="info-label">{{ t('modals.inventory.totalValue') }}</div>
          <div class="info-value total-value">
            {{ currencySymbol
            }}{{ totalValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}
          </div>
        </div>

        <div class="info-item">
          <div class="info-label">{{ t('modals.warehouse') }}</div>
          <div class="info-value">{{ translateWarehouse(inventoryItem.location) }}</div>
        </div>

        <div class="info-item">
          <div class="info-label">{{ t('modals.status') }}</div>
          <div class="info-value">
            <span :class="['badge', getStockStatusClass()]">
              {{ getStockStatus() }}
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

const { t, currentCurrency, translateProductName, translateWarehouse } = useI18n()

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

const currencySymbol = computed(() => {
  return currentCurrency.value === 'JPY' ? '¥' : '$'
})

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false,
  },
  inventoryItem: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['close'])

const totalValue = computed(() => {
  if (!props.inventoryItem) return 0
  return props.inventoryItem.quantity_on_hand * props.inventoryItem.unit_cost
})

const stockPercentage = computed(() => {
  if (!props.inventoryItem || props.inventoryItem.reorder_point === 0) return 0
  return Math.round((props.inventoryItem.quantity_on_hand / props.inventoryItem.reorder_point) * 100)
})

const close = () => {
  emit('close')
}

// Internal status key (drives CSS classes); the displayed label is translated in getStockStatus
const getStockStatusKey = () => {
  if (!props.inventoryItem) return 'Unknown'
  if (props.inventoryItem.quantity_on_hand <= props.inventoryItem.reorder_point) {
    return 'Low Stock'
  } else if (props.inventoryItem.quantity_on_hand <= props.inventoryItem.reorder_point * 1.5) {
    return 'Adequate'
  } else {
    return 'In Stock'
  }
}

const getStockStatus = () => {
  const labels = {
    'Low Stock': t('status.lowStock'),
    Adequate: t('status.adequate'),
    'In Stock': t('status.inStock'),
  }
  return labels[getStockStatusKey()] || t('modals.inventory.unknown')
}

const getStockStatusClass = () => {
  const status = getStockStatusKey()
  if (status === 'Low Stock') return 'danger'
  if (status === 'Adequate') return 'warning'
  return 'success'
}

const getStockIconClass = () => {
  const status = getStockStatusKey()
  if (status === 'Low Stock') return 'danger-icon'
  if (status === 'Adequate') return 'warning-icon'
  return 'success-icon'
}

const getSummaryCardClass = () => {
  const status = getStockStatusKey()
  if (status === 'Low Stock') return 'danger-card'
  if (status === 'Adequate') return 'warning-card'
  return 'success-card'
}
</script>

<style scoped>
.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-8);
}

.item-header {
  display: flex;
  align-items: center;
  gap: var(--space-5);
  padding-bottom: var(--space-6);
  border-bottom: 1px solid var(--border);
  margin-bottom: var(--space-6);
}

.item-icon {
  width: 64px;
  height: 64px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.item-icon.success-icon {
  background: var(--success);
}

.item-icon.warning-icon {
  background: var(--warning);
}

.item-icon.danger-icon {
  background: var(--danger);
}

.item-title-section {
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

.stock-summary {
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

.summary-card.primary {
  border-color: var(--info-border);
  background: var(--info-soft);
}

.summary-card.success-card {
  border-color: var(--success-border);
  background: var(--success-soft);
}

.summary-card.warning-card {
  border-color: var(--warning-border);
  background: var(--warning-soft);
}

.summary-card.danger-card {
  border-color: var(--danger-border);
  background: var(--danger-soft);
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

.summary-subtitle {
  font-size: var(--text-xs);
  color: var(--text-muted);
  margin-top: var(--space-1);
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

.info-value.total-value {
  font-size: var(--text-xl);
  color: var(--info);
  font-weight: 700;
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
