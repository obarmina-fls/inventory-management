<template>
  <div class="spending">
    <div class="page-header">
      <h2>{{ t('finance.title') }}</h2>
      <p>{{ t('finance.description') }}</p>
    </div>

    <AsyncStatus :loading="loading" :error="error" :loaded="loaded" @retry="reload">
      <!-- Revenue & Financial KPIs -->
      <div class="stats-grid-finance">
        <div class="stat-card revenue-card">
          <div class="stat-label">{{ t('finance.totalRevenue') }}</div>
          <div class="stat-value">{{ formatCurrency(revenueMetrics.totalRevenue) }}</div>
          <div class="stat-change positive">
            <span class="change-icon">↑</span>
            {{ t('finance.fromOrders', { count: revenueMetrics.orderCount }) }}
          </div>
        </div>
        <div class="stat-card cost-card">
          <div class="stat-label">{{ t('finance.totalCosts') }}</div>
          <div class="stat-value">{{ formatCurrency(totalCosts) }}</div>
          <div class="stat-meta">{{ t('finance.costBreakdown') }}</div>
        </div>
        <div class="stat-card profit-card">
          <div class="stat-label">{{ t('finance.netProfit') }}</div>
          <div class="stat-value">{{ formatCurrency(netProfit) }}</div>
          <div class="stat-meta">{{ profitMargin }}% {{ t('finance.margin') }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('finance.avgOrderValue') }}</div>
          <div class="stat-value">{{ formatCurrency(revenueMetrics.avgOrderValue) }}</div>
          <div class="stat-meta">{{ t('finance.perOrderRevenue') }}</div>
        </div>
      </div>

      <!-- Monthly Revenue vs Cost Chart -->
      <div class="card chart-card">
        <div class="card-header">
          <h3 class="card-title">{{ t('finance.revenueVsCosts.title') }}</h3>
          <div class="chart-legend">
            <span class="legend-item"
              ><span class="legend-dot revenue-color"></span>{{ t('finance.revenueVsCosts.revenue') }}</span
            >
            <span class="legend-item"
              ><span class="legend-dot cost-color"></span>{{ t('finance.revenueVsCosts.costs') }}</span
            >
          </div>
        </div>
        <div class="chart-container">
          <div class="bar-chart">
            <div class="y-axis">
              <span>{{ currencySymbol }}{{ maxRevenueValue }}K</span>
              <span>{{ currencySymbol }}{{ Math.round(maxRevenueValue * 0.75) }}K</span>
              <span>{{ currencySymbol }}{{ Math.round(maxRevenueValue * 0.5) }}K</span>
              <span>{{ currencySymbol }}{{ Math.round(maxRevenueValue * 0.25) }}K</span>
              <span>{{ currencySymbol }}0</span>
            </div>
            <div class="chart-area" role="img" :aria-label="revenueChartLabel">
              <div v-for="month in monthlyRevenue" :key="month.month" class="bar-group-revenue">
                <div class="revenue-bars">
                  <div
                    class="revenue-bar"
                    :style="{ height: getRevenueBarHeight(month.revenue) + '%' }"
                    :title="`Revenue: ${currencySymbol}${month.revenue.toLocaleString()}`"
                  ></div>
                  <div
                    class="cost-bar"
                    :style="{ height: getRevenueBarHeight(month.costs) + '%' }"
                    :title="`Costs: ${currencySymbol}${month.costs.toLocaleString()}`"
                  ></div>
                </div>
                <span class="bar-label">{{ translateMonth(month.month) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Monthly Cost Flow Chart -->
      <div class="card chart-card">
        <div class="card-header">
          <h3 class="card-title">{{ t('finance.monthlyCostFlow.title') }}</h3>
          <div class="chart-legend">
            <span class="legend-item"
              ><span class="legend-dot procurement"></span>{{ t('finance.monthlyCostFlow.procurement') }}</span
            >
            <span class="legend-item"
              ><span class="legend-dot operational"></span>{{ t('finance.monthlyCostFlow.operational') }}</span
            >
            <span class="legend-item"
              ><span class="legend-dot labor"></span>{{ t('finance.monthlyCostFlow.labor') }}</span
            >
            <span class="legend-item"
              ><span class="legend-dot overhead"></span>{{ t('finance.monthlyCostFlow.overhead') }}</span
            >
          </div>
        </div>
        <div class="chart-container">
          <div class="bar-chart">
            <div class="y-axis">
              <span>{{ currencySymbol }}25K</span>
              <span>{{ currencySymbol }}20K</span>
              <span>{{ currencySymbol }}15K</span>
              <span>{{ currencySymbol }}10K</span>
              <span>{{ currencySymbol }}5K</span>
              <span>{{ currencySymbol }}0</span>
            </div>
            <div class="chart-area" role="group" :aria-label="costFlowChartLabel">
              <div v-for="month in monthlySpending" :key="month.month" class="bar-group">
                <div
                  class="stacked-bar"
                  role="button"
                  tabindex="0"
                  :aria-label="t('finance.viewCostBreakdown', { month: translateMonth(month.month) })"
                  @click="showCostDetail(month)"
                  @keydown.enter.self.prevent="showCostDetail(month)"
                  @keydown.space.self.prevent="showCostDetail(month)"
                >
                  <div
                    class="bar-segment procurement"
                    :style="{ height: getBarHeight(month.procurement) + '%' }"
                    :title="`Procurement: ${currencySymbol}${month.procurement.toLocaleString()}`"
                  ></div>
                  <div
                    class="bar-segment operational"
                    :style="{ height: getBarHeight(month.operational) + '%' }"
                    :title="`Operational: ${currencySymbol}${month.operational.toLocaleString()}`"
                  ></div>
                  <div
                    class="bar-segment labor"
                    :style="{ height: getBarHeight(month.labor) + '%' }"
                    :title="`Labor: ${currencySymbol}${month.labor.toLocaleString()}`"
                  ></div>
                  <div
                    class="bar-segment overhead"
                    :style="{ height: getBarHeight(month.overhead) + '%' }"
                    :title="`Overhead: ${currencySymbol}${month.overhead.toLocaleString()}`"
                  ></div>
                </div>
                <span class="bar-label">{{ translateMonth(month.month) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="two-column-grid">
        <!-- Category Spending Breakdown -->
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">{{ t('finance.categorySpending.title') }}</h3>
          </div>
          <div class="category-list">
            <div v-for="category in categorySpending" :key="category.category" class="category-item">
              <div class="category-info">
                <div class="category-name">{{ translateCategory(category.category) }}</div>
                <div class="category-amount">{{ currencySymbol }}{{ category.amount.toLocaleString() }}</div>
              </div>
              <div class="category-bar-container">
                <div class="category-bar" :style="{ width: category.percentage + '%' }"></div>
              </div>
              <div class="category-meta">
                <span class="percentage">{{ category.percentage }}% {{ t('finance.categorySpending.ofTotal') }}</span>
                <span class="change" :class="{ positive: category.change > 0, negative: category.change < 0 }">
                  {{ category.change > 0 ? '+' : '' }}{{ category.change }}%
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Recent Transactions -->
        <div class="card transactions-card">
          <div class="card-header">
            <h3 class="card-title">{{ t('finance.transactions.title') }}</h3>
          </div>
          <div class="transactions-table-container">
            <table class="transactions-table">
              <thead>
                <tr>
                  <th>{{ t('finance.transactions.id') }}</th>
                  <th>{{ t('finance.transactions.description') }}</th>
                  <th>{{ t('finance.transactions.vendor') }}</th>
                  <th>{{ t('finance.transactions.date') }}</th>
                  <th class="text-right">{{ t('finance.transactions.amount') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="transaction in recentTransactions"
                  :key="transaction.id"
                  class="clickable-row"
                  tabindex="0"
                  @click="handleTransactionClick(transaction)"
                  @keydown.enter.self.prevent="handleTransactionClick(transaction)"
                  @keydown.space.self.prevent="handleTransactionClick(transaction)"
                >
                  <td class="transaction-id">{{ transaction.id.toString().padStart(3, '0') }}</td>
                  <td class="transaction-description">{{ transaction.description }}</td>
                  <td class="transaction-vendor">{{ transaction.vendor }}</td>
                  <td class="transaction-date">{{ formatDateShort(transaction.date) }}</td>
                  <td class="transaction-amount text-right">
                    {{ currencySymbol }}{{ transaction.amount.toLocaleString() }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </AsyncStatus>

    <TransactionDetailModal
      :is-open="showTransactionModal"
      :transaction="selectedTransaction"
      @close="showTransactionModal = false"
    />
    <CostDetailModal :is-open="showCostModal" :cost-data="selectedCostData" @close="showCostModal = false" />
  </div>
</template>

<script>
import AsyncStatus from '../components/AsyncStatus.vue'
import { useAsyncData } from '../composables/useAsyncData'
import { ref, computed } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrency as formatCurrencyUtil } from '../utils/currency'
import CostDetailModal from '../components/CostDetailModal.vue'
import TransactionDetailModal from '../components/TransactionDetailModal.vue'

export default {
  name: 'Spending',
  components: {
    AsyncStatus,
    CostDetailModal,
    TransactionDetailModal,
  },
  setup() {
    const { t, currentCurrency } = useI18n()
    const allMonthlySpending = ref([])
    const allCategorySpending = ref([])
    const allTransactions = ref([])
    const summaryData = ref({})
    // Per-month revenue/order counts from /api/reports/monthly-trends (filtered server-side)
    const monthlyTrends = ref([])

    // Modal state
    const showCostModal = ref(false)
    const selectedCostData = ref(null)
    const showTransactionModal = ref(false)
    const selectedTransaction = ref(null)

    // Use shared filters
    const { selectedPeriod } = useFilters()

    // Monthly spending chart always shows all months (not filtered)
    const monthlySpending = computed(() => {
      return allMonthlySpending.value
    })

    // Filtered monthly spending for summary calculations only
    const filteredMonthlySpending = computed(() => {
      if (selectedPeriod.value === 'all') {
        return allMonthlySpending.value
      }

      // Extract month name from YYYY-MM format
      const monthMap = {
        '01': 'Jan',
        '02': 'Feb',
        '03': 'Mar',
        '04': 'Apr',
        '05': 'May',
        '06': 'Jun',
        '07': 'Jul',
        '08': 'Aug',
        '09': 'Sep',
        10: 'Oct',
        11: 'Nov',
        12: 'Dec',
      }
      const selectedMonth = monthMap[selectedPeriod.value.split('-')[1]]
      return allMonthlySpending.value.filter((m) => m.month === selectedMonth)
    })

    const categorySpending = computed(() => {
      return allCategorySpending.value
    })

    const recentTransactions = computed(() => {
      if (selectedPeriod.value === 'all') {
        return allTransactions.value
      }
      // Filter transactions by selected month
      return allTransactions.value.filter((t) => {
        const transactionMonth = new Date(t.date).toISOString().slice(0, 7)
        return transactionMonth === selectedPeriod.value
      })
    })

    const summary = computed(() => {
      // Recalculate summary based on filteredMonthlySpending (not the chart data)
      if (filteredMonthlySpending.value.length === 0) {
        return summaryData.value
      }

      const totals = filteredMonthlySpending.value.reduce(
        (acc, month) => ({
          procurement: acc.procurement + month.procurement,
          operational: acc.operational + month.operational,
          labor: acc.labor + month.labor,
          overhead: acc.overhead + month.overhead,
        }),
        { procurement: 0, operational: 0, labor: 0, overhead: 0 }
      )

      return {
        total_procurement_cost: totals.procurement,
        total_operational_cost: totals.operational,
        total_labor_cost: totals.labor,
        total_overhead: totals.overhead,
        procurement_change: summaryData.value.procurement_change || 0,
        operational_change: summaryData.value.operational_change || 0,
        labor_change: summaryData.value.labor_change || 0,
        overhead_change: summaryData.value.overhead_change || 0,
      }
    })

    // Trend rows in the selected period (YYYY-MM). The chart below always shows all months.
    const periodTrends = computed(() => {
      if (selectedPeriod.value === 'all') return monthlyTrends.value
      return monthlyTrends.value.filter((m) => m.month === selectedPeriod.value)
    })

    // Revenue metrics from the filtered monthly trends
    const revenueMetrics = computed(() => {
      const totalRevenue = periodTrends.value.reduce((sum, m) => sum + (m.revenue || 0), 0)
      const orderCount = periodTrends.value.reduce((sum, m) => sum + (m.order_count || 0), 0)
      const avgOrderValue = orderCount > 0 ? totalRevenue / orderCount : 0

      return {
        totalRevenue,
        orderCount,
        avgOrderValue,
        revenueGrowth: 15.3, // Placeholder - could calculate from historical data
      }
    })

    // Total costs from summary
    const totalCosts = computed(() => {
      return (
        summary.value.total_procurement_cost +
        summary.value.total_operational_cost +
        summary.value.total_labor_cost +
        summary.value.total_overhead
      )
    })

    // Net profit
    const netProfit = computed(() => {
      return revenueMetrics.value.totalRevenue - totalCosts.value
    })

    // Profit margin percentage
    const profitMargin = computed(() => {
      if (revenueMetrics.value.totalRevenue === 0) return 0
      return ((netProfit.value / revenueMetrics.value.totalRevenue) * 100).toFixed(1)
    })

    // Monthly revenue data for chart
    const monthlyRevenue = computed(() => {
      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

      // Initialize all months
      const revenueByMonth = monthNames.map((month) => ({
        month,
        revenue: 0,
        costs: 0,
      }))

      // Revenue per month from the server (month is 'YYYY-MM'; months with no orders are absent)
      monthlyTrends.value.forEach((trend) => {
        const monthIndex = parseInt(String(trend.month).slice(5, 7), 10) - 1
        if (monthIndex >= 0 && monthIndex < 12) {
          revenueByMonth[monthIndex].revenue += trend.revenue || 0
        }
      })

      // Add costs from spending data
      allMonthlySpending.value.forEach((spending) => {
        const monthIndex = monthNames.indexOf(spending.month)
        if (monthIndex >= 0) {
          revenueByMonth[monthIndex].costs =
            spending.procurement + spending.operational + spending.labor + spending.overhead
        }
      })

      return revenueByMonth
    })

    // Max value for chart scaling
    const maxRevenueValue = computed(() => {
      const maxRevenue = Math.max(...monthlyRevenue.value.map((m) => m.revenue))
      const maxCost = Math.max(...monthlyRevenue.value.map((m) => m.costs))
      const max = Math.max(maxRevenue, maxCost)
      return Math.ceil(max / 1000) // Return in K
    })

    // Spending is period-only: the cost endpoints have no warehouse/category/status dimension, so revenue is
    // requested unfiltered too (same scope for Net Profit/Margin). Period is applied client-side via computed,
    // and the trends request omits `month` so the chart keeps showing every month. Loads once; reload is for Retry.
    const { loading, error, loaded, reload } = useAsyncData(
      async ({ signal }) => {
        const [summaryRes, monthlyRes, categoryRes, transactionsRes, trendsRes] = await Promise.all([
          api.getSpendingSummary({ signal }),
          api.getMonthlySpending({ signal }),
          api.getCategorySpending({ signal }),
          api.getTransactions({ signal }),
          api.getMonthlyTrends({}, { signal }),
        ])
        return { summaryRes, monthlyRes, categoryRes, transactionsRes, trendsRes }
      },
      {
        onSuccess: ({ summaryRes, monthlyRes, categoryRes, transactionsRes, trendsRes }) => {
          summaryData.value = summaryRes
          allMonthlySpending.value = monthlyRes
          allCategorySpending.value = categoryRes
          allTransactions.value = transactionsRes
          monthlyTrends.value = trendsRes
        },
      }
    )

    const formatCurrency = (value) => {
      return formatCurrencyUtil(value, currentCurrency.value)
    }

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const getBarHeight = (value) => {
      const maxValue = 25000
      return (value / maxValue) * 100
    }

    const getRevenueBarHeight = (value) => {
      const maxValue = maxRevenueValue.value * 1000
      // No revenue at all (empty filter result): avoid 0/0
      return maxValue > 0 ? (value / maxValue) * 100 : 0
    }

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      })
    }

    const formatDateShort = (dateString) => {
      const date = new Date(dateString)
      const month = (date.getMonth() + 1).toString().padStart(2, '0')
      const day = date.getDate().toString().padStart(2, '0')
      const year = date.getFullYear().toString().slice(-2)
      return `${month}/${day}/${year}`
    }

    const translateMonth = (month) => {
      const monthMap = {
        Jan: t('months.jan'),
        Feb: t('months.feb'),
        Mar: t('months.mar'),
        Apr: t('months.apr'),
        May: t('months.may'),
        Jun: t('months.jun'),
        Jul: t('months.jul'),
        Aug: t('months.aug'),
        Sep: t('months.sep'),
        Oct: t('months.oct'),
        Nov: t('months.nov'),
        Dec: t('months.dec'),
      }
      return monthMap[month] || month
    }

    const translateCategory = (category) => {
      // First try spending categories
      const spendingCategoryMap = {
        'Raw Materials': t('spendingCategories.rawMaterials'),
        Components: t('spendingCategories.components'),
        Equipment: t('spendingCategories.equipment'),
        Consumables: t('spendingCategories.consumables'),
      }

      // Then try product categories
      const productCategoryMap = {
        'Circuit Boards': t('categories.circuitBoards'),
        Sensors: t('categories.sensors'),
        Actuators: t('categories.actuators'),
        Controllers: t('categories.controllers'),
        'Power Supplies': t('categories.powerSupplies'),
      }

      return spendingCategoryMap[category] || productCategoryMap[category] || category
    }

    const handleTransactionClick = (transaction) => {
      selectedTransaction.value = transaction
      showTransactionModal.value = true
    }

    // Accessible text alternatives for the bar charts (values are otherwise only in hover titles)
    const revenueChartLabel = computed(() => {
      const parts = monthlyRevenue.value.map((m) =>
        t('finance.chartLabels.revenueItem', {
          month: translateMonth(m.month),
          // Rounded: revenue values carry cents that add noise when read aloud
          revenue: `${currencySymbol.value}${Math.round(m.revenue).toLocaleString()}`,
          costs: `${currencySymbol.value}${Math.round(m.costs).toLocaleString()}`,
        })
      )
      return `${t('finance.revenueVsCosts.title')}: ${parts.join('; ')}`
    })

    const costFlowChartLabel = computed(() => {
      const parts = monthlySpending.value.map((m) =>
        t('finance.chartLabels.costItem', {
          month: translateMonth(m.month),
          procurement: `${currencySymbol.value}${m.procurement.toLocaleString()}`,
          operational: `${currencySymbol.value}${m.operational.toLocaleString()}`,
          labor: `${currencySymbol.value}${m.labor.toLocaleString()}`,
          overhead: `${currencySymbol.value}${m.overhead.toLocaleString()}`,
        })
      )
      return `${t('finance.monthlyCostFlow.title')}: ${parts.join('; ')}`
    })

    const showCostDetail = (monthData) => {
      selectedCostData.value = monthData
      showCostModal.value = true
    }

    return {
      t,
      loading,
      error,
      loaded,
      reload,
      summary,
      monthlySpending,
      categorySpending,
      recentTransactions,
      revenueMetrics,
      totalCosts,
      netProfit,
      profitMargin,
      monthlyRevenue,
      maxRevenueValue,
      formatCurrency,
      currencySymbol,
      getBarHeight,
      getRevenueBarHeight,
      formatDate,
      formatDateShort,
      translateMonth,
      translateCategory,
      handleTransactionClick,
      showCostModal,
      selectedCostData,
      showCostDetail,
      showTransactionModal,
      selectedTransaction,
      revenueChartLabel,
      costFlowChartLabel,
      Math,
    }
  },
}
</script>

<style scoped>
.stat-change {
  margin-top: var(--space-3);
  font-size: var(--text-base);
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.stat-change.positive {
  color: var(--success-ink);
}

.stat-change.negative {
  color: var(--danger);
}

.change-icon {
  font-weight: 700;
  font-size: var(--text-lg);
}

.chart-card {
  margin-bottom: var(--space-6);
}

.card-header {
  flex-wrap: wrap;
}

.chart-legend {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2) var(--space-6);
  font-size: var(--text-base);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--text-muted);
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: var(--radius-sm);
}

.legend-dot.procurement {
  background: var(--info);
}
.legend-dot.operational {
  background: var(--violet);
}
.legend-dot.labor {
  background: var(--success);
}
.legend-dot.overhead {
  background: var(--warning);
}
.legend-dot.revenue-color {
  background: var(--text);
}
.legend-dot.cost-color {
  background: var(--danger);
}

.stats-grid-finance {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--space-6);
  margin-bottom: var(--space-8);
}

.revenue-card {
  --status-color: var(--text);
}

.cost-card {
  --status-color: var(--danger);
}

.profit-card {
  --status-color: var(--info);
}

.stat-meta {
  margin-top: var(--space-2);
  font-size: var(--text-sm);
  color: var(--text-muted);
}

.bar-group-revenue {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  min-width: 0;
  height: 100%;
}

.revenue-bars {
  width: 100%;
  max-width: 80px;
  display: flex;
  gap: var(--space-1);
  justify-content: center;
  align-items: flex-end;
  height: 100%;
  padding-bottom: var(--space-8);
}

.revenue-bar,
.cost-bar {
  width: 50%;
  max-width: 30px;
  border-radius: var(--radius-md) var(--radius-md) 0 0;
  transition: all 0.3s ease;
  cursor: pointer;
  min-height: 4px;
}

.revenue-bar {
  background: var(--text);
}

.cost-bar {
  background: var(--danger);
}

.revenue-bar:hover,
.cost-bar:hover {
  opacity: 0.8;
  transform: scaleY(1.05);
}

.chart-container {
  padding: var(--space-6) 0;
}

.bar-chart {
  display: flex;
  gap: var(--space-6);
  height: 350px;
}

.y-axis {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding-right: var(--space-4);
  font-size: var(--text-xs);
  color: var(--text-subtle);
  border-right: 1px solid var(--border);
}

.chart-area {
  flex: 1;
  /* Allow shrinking below content width so the chart fits narrow screens */
  min-width: 0;
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  gap: var(--space-2);
}

.bar-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  min-width: 0;
  height: 100%;
}

.stacked-bar {
  width: 100%;
  max-width: 60px;
  display: flex;
  flex-direction: column-reverse;
  align-items: stretch;
  height: 100%;
  padding-bottom: var(--space-8);
  cursor: pointer;
  transition: opacity var(--duration) var(--ease);
}

.stacked-bar:hover {
  opacity: 0.85;
}

.stacked-bar:focus-visible {
  outline: 2px solid var(--focus-color);
  outline-offset: 2px;
  box-shadow: none;
}

.bar-segment {
  width: 100%;
  transition: all 0.3s ease;
  cursor: pointer;
  display: block;
}

.bar-segment:first-child {
  border-radius: 0 0 var(--radius-md) var(--radius-md);
}

.bar-segment:last-child {
  border-radius: var(--radius-md) var(--radius-md) 0 0;
}

.bar-segment.procurement {
  background: var(--info);
}
.bar-segment.operational {
  background: var(--violet);
}
.bar-segment.labor {
  background: var(--success);
}
.bar-segment.overhead {
  background: var(--warning);
}

.bar-segment:hover {
  opacity: 0.8;
}

.bar-label {
  margin-top: var(--space-2);
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--text-muted);
}

.two-column-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(450px, 100%), 1fr));
  gap: var(--space-6);
}

.category-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.category-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.category-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.category-name {
  font-weight: 600;
  color: var(--text);
}

.category-amount {
  font-weight: 700;
  color: var(--info);
  font-size: var(--text-xl);
}

.category-bar-container {
  width: 100%;
  height: 8px;
  background: var(--surface-muted);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.category-bar {
  height: 100%;
  background: var(--info);
  border-radius: var(--radius-sm);
  transition: width 0.6s ease;
}

.category-meta {
  display: flex;
  justify-content: space-between;
  font-size: var(--text-sm);
}

.percentage {
  color: var(--text-muted);
}

.change {
  font-weight: 600;
}

.change.positive {
  color: var(--success-ink);
}

.change.negative {
  color: var(--danger);
}

.transactions-card {
  display: flex;
  flex-direction: column;
}

.transactions-table-container {
  overflow-y: auto;
  max-height: 400px;
}

.transactions-table {
  width: 100%;
  border-collapse: collapse;
}

.transactions-table thead {
  position: sticky;
  top: 0;
  background: var(--surface-subtle);
  z-index: 1;
}

.transactions-table th {
  text-align: left;
  padding: var(--space-2) var(--space-3);
  font-weight: 600;
  color: var(--text-secondary);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid var(--border);
}

.transactions-table th.text-right {
  text-align: right;
}

.transactions-table td {
  padding: var(--space-3) var(--space-3);
  border-bottom: 1px solid var(--surface-muted);
  font-size: var(--text-base);
}

.transactions-table tbody tr {
  cursor: pointer;
  transition: background-color var(--duration) var(--ease);
}

.transactions-table tbody tr:hover {
  background: var(--surface-subtle);
}

.transactions-table tbody tr.clickable-row:hover {
  background: var(--info-soft);
}

.transaction-id {
  color: var(--text-muted);
  font-weight: 500;
  font-family: var(--font-mono);
  font-size: var(--text-sm);
}

.transaction-description {
  color: var(--text);
  font-weight: 500;
}

.transaction-vendor {
  color: var(--text-muted);
}

.transaction-date {
  color: var(--text-muted);
  font-size: var(--text-sm);
}

.transaction-amount {
  font-weight: 700;
  color: var(--text);
}

.text-right {
  text-align: right;
}
</style>
