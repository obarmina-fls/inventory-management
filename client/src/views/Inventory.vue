<template>
  <div class="inventory">
    <div class="page-header">
      <h2>{{ t('inventory.title') }}</h2>
      <p>{{ t('inventory.description') }}</p>
    </div>

    <AsyncStatus :loading="loading" :error="error" :loaded="loaded" @retry="reload">
      <div class="card">
        <div class="card-header">
          <h3 ref="stockTitle" class="card-title" tabindex="-1">
            {{ t('inventory.stockLevels') }} ({{ filteredItems.length }} {{ t('inventory.skus') }})
          </h3>
          <button
            type="button"
            class="btn-primary restock-all"
            :disabled="lowStockItems.length === 0"
            @click="openRestock(lowStockItems)"
          >
            {{ t('inventory.restockLowStock', { n: lowStockItems.length }) }}
          </button>
          <div class="search-box">
            <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path
                fill-rule="evenodd"
                d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z"
                clip-rule="evenodd"
              />
            </svg>
            <input
              v-model="searchQuery"
              type="text"
              :placeholder="t('inventory.searchPlaceholder')"
              :aria-label="t('inventory.searchLabel')"
              class="search-input"
            />
            <button
              v-if="searchQuery"
              @click="searchQuery = ''"
              class="clear-search"
              :title="t('inventory.clearSearch')"
              :aria-label="t('inventory.clearSearch')"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fill-rule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clip-rule="evenodd"
                />
              </svg>
            </button>
          </div>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('inventory.table.sku') }}</th>
                <th>{{ t('inventory.table.itemName') }}</th>
                <th>{{ t('inventory.table.category') }}</th>
                <th class="num">{{ t('inventory.table.quantityOnHand') }}</th>
                <th class="num">{{ t('inventory.table.reorderPoint') }}</th>
                <th class="num">{{ t('inventory.table.unitCost') }}</th>
                <th class="num">{{ t('inventory.table.totalValue') }}</th>
                <th>{{ t('inventory.table.location') }}</th>
                <th>{{ t('inventory.table.status') }}</th>
                <th><span class="sr-only">{{ t('inventory.restockRow') }}</span></th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="filteredItems.length === 0">
                <td colspan="10" class="table-empty-cell">
                  <div>{{ t('common.noMatch') }}</div>
                  <button type="button" class="btn-reset" @click="resetAll">
                    {{ t('common.resetFiltersAndSearch') }}
                  </button>
                </td>
              </tr>
              <tr
                v-for="item in pagedItems"
                :key="item.id"
                class="clickable-row"
                tabindex="0"
                @click="showItemDetail(item)"
                @keydown.enter.self.prevent="showItemDetail(item)"
                @keydown.space.self.prevent="showItemDetail(item)"
              >
                <td class="mono">
                  <strong>{{ item.sku }}</strong>
                </td>
                <td>{{ translateProductName(item.name) }}</td>
                <td>{{ translateCategory(item.category) }}</td>
                <td class="num">
                  <strong>{{ item.quantity_on_hand }}</strong>
                </td>
                <td class="num">{{ item.reorder_point }}</td>
                <td class="num">{{ currencySymbol }}{{ item.unit_cost.toFixed(2) }}</td>
                <td class="num">
                  <strong
                    >{{ currencySymbol
                    }}{{
                      (item.quantity_on_hand * item.unit_cost).toLocaleString(undefined, {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })
                    }}</strong
                  >
                </td>
                <td>{{ translateWarehouse(item.location) }}</td>
                <td>
                  <span :class="['badge', getStockStatusClass(item)]">
                    {{ getStockStatus(item) }}
                  </span>
                </td>
                <td>
                  <button
                    v-if="isLowStock(item)"
                    type="button"
                    class="btn-row"
                    :aria-label="t('inventory.restockRowLabel', { sku: item.sku })"
                    @click.stop="openRestock([item])"
                    @keydown.enter.stop
                    @keydown.space.stop
                  >
                    {{ t('inventory.restockRow') }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <BasePagination :page="page" :page-size="PAGE_SIZE" :total="filteredItems.length" @update:page="onPageChange" />
      </div>
    </AsyncStatus>

    <InventoryDetailModal :is-open="showItemModal" :inventory-item="selectedItem" @close="showItemModal = false" />
    <RestockModal :show="showRestockModal" :items="restockItems" @close="showRestockModal = false" />
  </div>
</template>

<script>
import AsyncStatus from '../components/AsyncStatus.vue'
import BasePagination from '../components/BasePagination.vue'
import { useAsyncData } from '../composables/useAsyncData'
import { ref, computed, watch, nextTick } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import InventoryDetailModal from '../components/InventoryDetailModal.vue'
import RestockModal from '../components/RestockModal.vue'

export default {
  name: 'Inventory',
  components: {
    AsyncStatus,
    BasePagination,
    InventoryDetailModal,
    RestockModal,
  },
  setup() {
    const { t, currentCurrency, translateProductName, translateWarehouse } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const items = ref([])
    const searchQuery = ref('')

    // Modal state
    const showItemModal = ref(false)
    const selectedItem = ref(null)

    // Use shared filters
    const { selectedLocation, selectedCategory, getCurrentFilters, resetFilters } = useFilters()

    // Empty-state action: clear the global filters and the local search box
    const resetAll = () => {
      resetFilters()
      searchQuery.value = ''
    }

    // Stock status order for sorting (using status keys)
    const STATUS_ORDER = { lowStock: 0, adequate: 1, inStock: 2 }

    // Get stock status key (for sorting and translation)
    const getStockStatusKey = (item) => {
      if (item.quantity_on_hand <= item.reorder_point) {
        return 'lowStock'
      } else if (item.quantity_on_hand <= item.reorder_point * 1.5) {
        return 'adequate'
      } else {
        return 'inStock'
      }
    }

    // Computed property to filter items by search query and sort by stock status
    const filteredItems = computed(() => {
      let filtered = items.value

      // Apply search filter if query exists
      if (searchQuery.value.trim()) {
        const query = searchQuery.value.toLowerCase().trim()
        filtered = filtered.filter((item) => item.name.toLowerCase().includes(query))
      }

      // Sort by stock status: Low Stock first, then Adequate, then In Stock
      // Always create a copy to avoid mutating the original array
      return filtered.slice().sort((a, b) => {
        const statusA = getStockStatusKey(a)
        const statusB = getStockStatusKey(b)
        return STATUS_ORDER[statusA] - STATUS_ORDER[statusB]
      })
    })

    // Reloads on filter change; previous items stay visible meanwhile
    const { loading, error, loaded, reload } = useAsyncData(
      ({ signal }) => {
        const filters = getCurrentFilters()
        // Inventory doesn't support month/status filters, only warehouse and category
        return api.getInventory(
          {
            warehouse: filters.warehouse,
            category: filters.category,
          },
          { signal }
        )
      },
      {
        watchSources: [selectedLocation, selectedCategory],
        onSuccess: (result) => {
          items.value = result
        },
      }
    )

    // Client-side paging over the filtered + sorted list (the heading count stays the full total)
    const PAGE_SIZE = 25
    const page = ref(1)
    const stockTitle = ref(null)

    // Clamp: a refetch or narrower search can leave the current page past the end
    const pageCount = computed(() => Math.max(1, Math.ceil(filteredItems.value.length / PAGE_SIZE)))
    watch(pageCount, (count) => {
      if (page.value > count) page.value = count
    })
    // Warehouse/category filter or search text change -> back to page 1
    watch([selectedLocation, selectedCategory, searchQuery], () => {
      page.value = 1
    })

    const pagedItems = computed(() => {
      const start = (page.value - 1) * PAGE_SIZE
      return filteredItems.value.slice(start, start + PAGE_SIZE)
    })

    // Only user-initiated page changes move focus, so keyboard users are not left at the old bottom position
    const onPageChange = async (next) => {
      page.value = next
      await nextTick()
      stockTitle.value?.focus({ preventScroll: true })
      stockTitle.value?.scrollIntoView({ block: 'start' })
    }

    const getStockStatus = (item) => {
      const key = getStockStatusKey(item)
      return t(`status.${key}`)
    }

    const getStockStatusClass = (item) => {
      if (item.quantity_on_hand <= item.reorder_point) {
        return 'danger'
      } else if (item.quantity_on_hand <= item.reorder_point * 1.5) {
        return 'warning'
      } else {
        return 'success'
      }
    }

    const translateCategory = (category) => {
      const categoryMap = {
        'Circuit Boards': t('categories.circuitBoards'),
        Sensors: t('categories.sensors'),
        Actuators: t('categories.actuators'),
        Controllers: t('categories.controllers'),
        'Power Supplies': t('categories.powerSupplies'),
      }
      return categoryMap[category] || category
    }

    // Low stock = at or below reorder point (same rule as the 'lowStock' status)
    const isLowStock = (item) => getStockStatusKey(item) === 'lowStock'
    // All low-stock items of the filtered list (not just the current page)
    const lowStockItems = computed(() => filteredItems.value.filter(isLowStock))

    const showRestockModal = ref(false)
    const restockItems = ref([])
    const openRestock = (list) => {
      restockItems.value = list.slice()
      showRestockModal.value = true
    }

    const showItemDetail = (item) => {
      selectedItem.value = item
      showItemModal.value = true
    }

    return {
      t,
      loading,
      error,
      loaded,
      reload,
      items,
      searchQuery,
      resetAll,
      filteredItems,
      pagedItems,
      page,
      PAGE_SIZE,
      onPageChange,
      stockTitle,
      getStockStatus,
      getStockStatusClass,
      translateCategory,
      showItemModal,
      selectedItem,
      showItemDetail,
      isLowStock,
      lowStockItems,
      showRestockModal,
      restockItems,
      openRestock,
      currencySymbol,
      translateProductName,
      translateWarehouse,
    }
  },
}
</script>

<style scoped>
.card-header {
  flex-wrap: wrap;
}

.restock-all {
  margin-left: auto;
}

.btn-row {
  height: 28px;
  padding: 0 var(--space-3);
  background: var(--surface);
  color: var(--danger-ink);
  border: 1px solid var(--danger-border);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}

.btn-row:hover {
  background: var(--danger-soft);
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
  min-width: min(300px, 100%);
}

.search-icon {
  position: absolute;
  left: var(--space-3);
  width: 18px;
  height: 18px;
  color: var(--text-subtle);
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: var(--space-2) var(--space-10) var(--space-2) var(--space-10);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-lg);
  font-size: var(--text-base);
  color: var(--text);
  background: var(--surface-subtle);
  transition: all var(--duration) var(--ease);
}

.search-input:focus {
  outline: none;
  border-color: var(--info);
  background: var(--surface);
  box-shadow: var(--focus-ring);
}

.search-input::placeholder {
  color: var(--text-muted);
}

.clear-search {
  position: absolute;
  right: var(--space-2);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-1);
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--text-subtle);
  cursor: pointer;
  transition: all var(--duration) var(--ease);
}

.clear-search:hover {
  background: var(--border);
  color: var(--text-muted);
}

.clear-search svg {
  width: 18px;
  height: 18px;
}
</style>
