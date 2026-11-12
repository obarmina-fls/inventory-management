<template>
  <BaseModal :open="show" :title="t('inventory.restock.title')" max-width="960px" @close="close">
    <div class="modal-body">
      <div v-if="order" class="confirmation" role="status">
        <strong>{{ t('inventory.restock.success', { orderNumber: order.order_number }) }}</strong>
        <span>
          {{
            t('inventory.restock.successSummary', {
              total: money(order.total_cost),
              delivery: formatDate(order.expected_delivery),
            })
          }}
        </span>
      </div>

      <template v-else>
        <p class="description">{{ t('inventory.restock.description') }}</p>

        <div v-if="rows.length === 0" class="empty-note">{{ t('inventory.restock.noItems') }}</div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('inventory.restock.sku') }}</th>
                <th>{{ t('inventory.restock.name') }}</th>
                <th>{{ t('inventory.restock.warehouse') }}</th>
                <th class="num">{{ t('inventory.restock.onHand') }}</th>
                <th class="num">{{ t('inventory.restock.reorderPoint') }}</th>
                <th class="num">{{ t('inventory.restock.unitCost') }}</th>
                <th class="num">{{ t('inventory.restock.quantity') }}</th>
                <th class="num">{{ t('inventory.restock.lineTotal') }}</th>
                <th><span class="sr-only">{{ t('inventory.restock.remove') }}</span></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in rows" :key="row.sku">
                <td class="mono">
                  <strong>{{ row.sku }}</strong>
                </td>
                <td>{{ translateProductName(row.name) }}</td>
                <td>{{ translateWarehouse(row.location) }}</td>
                <td class="num">{{ row.quantity_on_hand }}</td>
                <td class="num">{{ row.reorder_point }}</td>
                <td class="num">{{ money(row.unit_cost) }}</td>
                <td class="num">
                  <input
                    v-model.number="row.quantity"
                    type="number"
                    min="1"
                    :max="MAX_QTY"
                    step="1"
                    class="qty-input"
                    :class="{ invalid: !isValidQty(row.quantity) }"
                    :aria-label="t('inventory.restock.quantityLabel', { sku: row.sku })"
                  />
                </td>
                <td class="num">{{ isValidQty(row.quantity) ? money(row.quantity * row.unit_cost) : '-' }}</td>
                <td>
                  <button
                    type="button"
                    class="btn-secondary btn-small"
                    :disabled="submitting"
                    :aria-label="t('inventory.restock.removeLabel', { sku: row.sku })"
                    @click="removeRow(row.sku)"
                  >
                    {{ t('inventory.restock.remove') }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="rows.length > 0" class="order-total">
          <span>{{ t('inventory.restock.estimatedTotal') }}</span>
          <strong>{{ money(orderTotal) }}</strong>
        </div>
        <div v-if="showQtyHint && !allValid" class="field-error">{{ t('inventory.restock.quantityInvalid') }}</div>
        <div v-if="submitError" class="error" role="alert">{{ submitError }}</div>
      </template>
    </div>

    <div class="modal-footer">
      <button type="button" class="btn-secondary" @click="close">{{ t('common.close') }}</button>
      <button v-if="!order" type="button" class="btn-primary" :disabled="!canSubmit" @click="submit">
        {{ submitting ? t('inventory.restock.submitting') : t('inventory.restock.submit') }}
      </button>
    </div>
  </BaseModal>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { api } from '../api'
import BaseModal from './BaseModal.vue'
import { useI18n } from '../composables/useI18n'
import { formatCurrencyWithDecimals } from '../utils/currency'

const MAX_QTY = 100000

const props = defineProps({
  // Inventory items to restock
  items: { type: Array, default: () => [] },
  show: { type: Boolean, default: false },
})
const emit = defineEmits(['close', 'submitted'])

const { t, currentCurrency, currentLocale, translateProductName, translateWarehouse } = useI18n()

const rows = ref([])
const submitting = ref(false)
const submitError = ref('')
const order = ref(null)
const showQtyHint = ref(false)

// Order up to 2x the reorder point to leave a buffer above it, so the item does not
// drop straight back to low stock after the next few sales. Never less than 1 unit.
const suggestedQuantity = (item) => Math.max(1, 2 * item.reorder_point - item.quantity_on_hand)

// Rebuild the editable rows (local copies, props are never mutated) each time the modal opens
watch(
  () => [props.show, props.items],
  ([open]) => {
    if (!open) return
    rows.value = props.items.map((item) => ({ ...item, quantity: suggestedQuantity(item) }))
    submitting.value = false
    submitError.value = ''
    order.value = null
    showQtyHint.value = false
  },
  { immediate: true }
)

const isValidQty = (q) => Number.isInteger(q) && q >= 1 && q <= MAX_QTY
const allValid = computed(() => rows.value.every((r) => isValidQty(r.quantity)))
const canSubmit = computed(() => rows.value.length > 0 && !submitting.value)

// Estimate from inventory unit_cost; the server resolves the authoritative price
const orderTotal = computed(() =>
  rows.value.reduce((sum, r) => (isValidQty(r.quantity) ? sum + r.quantity * r.unit_cost : sum), 0)
)

const money = (amount) => formatCurrencyWithDecimals(Number(amount) || 0, currentCurrency.value, 2)

const formatDate = (value) => {
  const date = new Date(/^\d{4}-\d{2}-\d{2}$/.test(value) ? `${value}T00:00:00` : value)
  if (isNaN(date.getTime())) return ''
  return date.toLocaleDateString(currentLocale.value === 'ja' ? 'ja-JP' : 'en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

const removeRow = (sku) => {
  rows.value = rows.value.filter((r) => r.sku !== sku)
}

const close = () => emit('close')

const errorMessage = (err) => {
  const status = err?.response?.status
  const detail = err?.response?.data?.detail
  if (status === 409) return typeof detail === 'string' ? detail : t('inventory.restock.orderLimit')
  if (typeof detail === 'string') return detail
  // FastAPI 422 returns a list of { loc, msg } objects
  if (Array.isArray(detail)) return detail.map((d) => d.msg).join('; ')
  return t('inventory.restock.submitFailed')
}

const submit = async () => {
  if (!canSubmit.value) return
  submitError.value = ''
  showQtyHint.value = true
  if (!allValid.value) return
  submitting.value = true
  try {
    const result = await api.submitRestockOrder(rows.value.map(({ sku, quantity }) => ({ sku, quantity })))
    order.value = result
    emit('submitted', result)
  } catch (err) {
    submitError.value = errorMessage(err)
    console.error('Restock submit error:', err)
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-6);
}

.description {
  color: var(--text-muted);
  font-size: var(--text-base);
  margin-bottom: var(--space-4);
}

.qty-input {
  width: 96px;
  height: var(--control-height);
  padding: 0 var(--space-2);
  text-align: right;
  background: var(--surface);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-md);
  font-size: var(--text-base);
  color: var(--text);
}
.qty-input:focus {
  outline: none;
  border-color: var(--info);
  box-shadow: var(--focus-ring);
}
.qty-input.invalid {
  border-color: var(--danger);
}

.order-total {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-4);
  padding: var(--space-4) 0 0;
  font-size: var(--text-md);
  color: var(--text);
}

.field-error {
  margin-top: var(--space-2);
  font-size: var(--text-sm);
  color: var(--danger-ink);
}

.confirmation {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-4);
  background: var(--success-soft);
  border: 1px solid var(--success-border);
  border-radius: var(--radius-lg);
  color: var(--success-ink);
}

.empty-note {
  padding: var(--space-8);
  text-align: center;
  color: var(--text-muted);
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
.btn-secondary:hover:not(:disabled) {
  background: var(--border);
  border-color: var(--border-strong);
}
.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn-small {
  padding: var(--space-1) var(--space-3);
  font-size: var(--text-sm);
}
</style>
