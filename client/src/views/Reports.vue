<template>
  <div class="reports">
    <div class="page-header no-print">
      <div>
        <h2>{{ t('reports.title') }}</h2>
        <p>{{ t('reports.description') }}</p>
      </div>
      <!-- Two plain buttons instead of a menu: fewer states, native keyboard support -->
      <div class="export-actions" role="group" :aria-label="t('reports.export.group')">
        <button type="button" class="btn-primary" :disabled="exportDisabled" @click="exportCsv">
          {{ t('reports.export.button') }}
        </button>
        <button type="button" class="btn-primary" :disabled="exportDisabled" @click="exportPdf">
          {{ t('reports.export.pdfButton') }}
        </button>
      </div>
    </div>

    <!-- Visible only when printing: report title and the active filters -->
    <div class="print-only print-header">
      <h1>{{ t('reports.title') }}</h1>
      <p>
        <span v-for="f in filterSummary" :key="f.key" class="print-filter">{{ f.label }}: {{ f.value }}</span>
      </p>
    </div>

    <AsyncStatus
      :loading="loading"
      :error="error"
      :loaded="loaded"
      :loading-text="t('reports.loading')"
      @retry="reload"
    >
      <div v-if="quarterlyData.length === 0 && monthlyRows.length === 0" class="card empty-state">
        {{ t('reports.noData') }}
      </div>
      <div v-else>
        <!-- Quarterly Performance -->
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">{{ t('reports.quarterly.title') }}</h3>
          </div>
          <div v-if="quarterlyData.length === 0" class="empty-state">{{ t('reports.noData') }}</div>
          <div v-else class="table-container">
            <table class="reports-table">
              <thead>
                <tr>
                  <th>{{ t('reports.quarterly.quarter') }}</th>
                  <th class="num">{{ t('reports.quarterly.totalOrders') }}</th>
                  <th class="num">{{ t('reports.quarterly.totalRevenue') }}</th>
                  <th class="num">{{ t('reports.quarterly.avgOrderValue') }}</th>
                  <th>{{ t('reports.quarterly.fulfillmentRate') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="q in quarterlyData" :key="q.quarter">
                  <td>
                    <strong>{{ q.quarter }}</strong>
                  </td>
                  <td class="num">{{ q.total_orders }}</td>
                  <td class="num">{{ formatCurrency(q.total_revenue, currentCurrency) }}</td>
                  <td class="num">{{ formatCurrency(q.avg_order_value, currentCurrency) }}</td>
                  <td>
                    <span :class="getFulfillmentClass(q.fulfillment_rate)"> {{ q.fulfillment_rate }}% </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Monthly Trends Chart -->
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">{{ t('reports.trend.title') }}</h3>
          </div>
          <div v-if="monthlyRows.length === 0" class="empty-state">{{ t('reports.noData') }}</div>
          <div v-else class="chart-container">
            <div class="bar-chart">
              <div v-for="row in monthlyRows" :key="row.month" class="bar-wrapper">
                <div class="bar-container">
                  <div
                    class="bar"
                    :style="{ height: getBarHeight(row.revenue) + 'px' }"
                    :title="formatCurrency(row.revenue, currentCurrency)"
                  ></div>
                </div>
                <div class="bar-label">{{ row.label }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Month-over-Month Comparison -->
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">{{ t('reports.mom.title') }}</h3>
          </div>
          <div v-if="monthlyRows.length === 0" class="empty-state">{{ t('reports.noData') }}</div>
          <div v-else class="table-container">
            <table class="reports-table">
              <thead>
                <tr>
                  <th>{{ t('reports.mom.month') }}</th>
                  <th class="num">{{ t('reports.mom.orders') }}</th>
                  <th class="num">{{ t('reports.mom.revenue') }}</th>
                  <th>{{ t('reports.mom.change') }}</th>
                  <th>{{ t('reports.mom.growthRate') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in monthlyRows" :key="row.month">
                  <td>
                    <strong>{{ row.label }}</strong>
                  </td>
                  <td class="num">{{ row.order_count }}</td>
                  <td class="num">{{ formatCurrency(row.revenue, currentCurrency) }}</td>
                  <td>
                    <span v-if="row.hasPrevious" :class="row.changeClass">{{ row.changeText }}</span>
                    <span v-else>-</span>
                  </td>
                  <td>
                    <span v-if="row.hasPrevious" :class="row.changeClass">{{ row.growthText }}</span>
                    <span v-else>-</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Summary Stats -->
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-label">{{ t('reports.stats.totalRevenue') }}</div>
            <div class="stat-value">{{ formatCurrency(totalRevenue, currentCurrency) }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">{{ t('reports.stats.avgMonthlyRevenue') }}</div>
            <div class="stat-value">{{ formatCurrency(avgMonthlyRevenue, currentCurrency) }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">{{ t('reports.stats.totalOrders') }}</div>
            <div class="stat-value">{{ totalOrders }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">{{ t('reports.stats.bestQuarter') }}</div>
            <div class="stat-value">{{ bestQuarter || '-' }}</div>
          </div>
        </div>
      </div>
    </AsyncStatus>
  </div>
</template>

<script>
import AsyncStatus from '../components/AsyncStatus.vue'
import { useAsyncData } from '../composables/useAsyncData'
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'
import { buildCsv, toCsvLine, downloadCsv } from '../utils/csv'

const MONTH_KEYS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

export default {
  name: 'Reports',
  components: { AsyncStatus },
  setup() {
    const { t, currentCurrency } = useI18n()

    // Raw data in refs; everything derived is computed
    const quarterlyData = ref([])
    const monthlyData = ref([])

    const { selectedPeriod, selectedLocation, selectedCategory, selectedStatus, getCurrentFilters } = useFilters()

    // Reloads on filter change; previous data stays visible meanwhile
    const { loading, error, loaded, reload } = useAsyncData(
      async ({ signal }) => {
        const filters = getCurrentFilters()
        // Independent requests: run in parallel
        const [quarterly, monthly] = await Promise.all([
          api.getQuarterlyReports(filters, { signal }),
          api.getMonthlyTrends(filters, { signal }),
        ])
        return { quarterly, monthly }
      },
      {
        watchSources: [selectedPeriod, selectedLocation, selectedCategory, selectedStatus],
        onSuccess: ({ quarterly, monthly }) => {
          quarterlyData.value = quarterly
          monthlyData.value = monthly
        },
      }
    )

    // 'YYYY-MM' -> localized month label; falls back to the raw string if malformed
    const formatMonth = (monthStr) => {
      const [year, month] = String(monthStr).split('-')
      const key = MONTH_KEYS[parseInt(month, 10) - 1]
      return key ? `${t('months.' + key)} ${year}` : monthStr
    }

    const maxRevenue = computed(() => monthlyData.value.reduce((max, m) => Math.max(max, m.revenue), 0))

    // Chart bar height in px (max 200)
    const getBarHeight = (revenue) => {
      return maxRevenue.value === 0 ? 0 : (revenue / maxRevenue.value) * 200
    }

    // Monthly rows with label and month-over-month change precomputed
    const monthlyRows = computed(() => {
      return monthlyData.value.map((m, index) => {
        const row = { ...m, label: formatMonth(m.month), hasPrevious: index > 0 }
        if (index > 0) {
          const prev = monthlyData.value[index - 1].revenue
          const change = m.revenue - prev
          const sign = change > 0 ? '+' : change < 0 ? '-' : ''
          row.changeText = sign + formatCurrencyWithDecimals(Math.abs(change), currentCurrency.value, 2)
          row.changeClass = change > 0 ? 'positive-change' : change < 0 ? 'negative-change' : ''
          // Growth is undefined when previous month had no revenue
          // Raw numbers for CSV export, rounded to 1 decimal; growth stays null when prev is 0
          row.changeValue = Math.round(change * 10) / 10
          row.growthValue = prev === 0 ? null : Math.round((change / prev) * 1000) / 10
          row.growthText = prev === 0 ? 'N/A' : (change > 0 ? '+' : '') + ((change / prev) * 100).toFixed(1) + '%'
        }
        return row
      })
    })

    const totalRevenue = computed(() => monthlyData.value.reduce((sum, m) => sum + m.revenue, 0))

    const avgMonthlyRevenue = computed(() =>
      monthlyData.value.length > 0 ? totalRevenue.value / monthlyData.value.length : 0
    )

    const totalOrders = computed(() => monthlyData.value.reduce((sum, m) => sum + m.order_count, 0))

    // Empty string when there is no quarter with revenue
    const bestQuarter = computed(() => {
      let best = null
      for (const q of quarterlyData.value) {
        if (q.total_revenue > 0 && (!best || q.total_revenue > best.total_revenue)) best = q
      }
      return best ? best.quarter : ''
    })

    const getFulfillmentClass = (rate) => {
      if (rate >= 90) return 'badge success'
      if (rate >= 75) return 'badge warning'
      return 'badge danger'
    }

    // Disabled while loading or when there is nothing to export
    const exportDisabled = computed(
      () => loading.value || (quarterlyData.value.length === 0 && monthlyData.value.length === 0)
    )

    // Active filter value as a readable label ('all' -> localized "All")
    const filterLabel = (value, statusKey = false) => {
      if (value === 'all') return t('filters.all')
      return statusKey ? t('status.' + value) : value
    }

    // Active filters as label/value pairs; shared by the CSV export and the print header
    const filterSummary = computed(() => [
      { key: 'period', label: t('reports.export.period'), value: filterLabel(selectedPeriod.value) },
      { key: 'warehouse', label: t('reports.export.warehouse'), value: filterLabel(selectedLocation.value) },
      { key: 'category', label: t('reports.export.category'), value: filterLabel(selectedCategory.value) },
      { key: 'status', label: t('reports.export.status'), value: filterLabel(selectedStatus.value, true) },
    ])

    // Local date (not UTC) so the filename matches the user's calendar day
    const reportBaseName = () => {
      const d = new Date()
      const pad = (n) => String(n).padStart(2, '0')
      return `report-${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
    }

    // "Save as PDF" uses document.title as the suggested filename. Set it for the
    // print and restore it on afterprint (also fires when the dialog is cancelled).
    let originalTitle = null
    const restoreTitle = () => {
      if (originalTitle !== null) {
        document.title = originalTitle
        originalTitle = null
      }
    }
    const exportPdf = () => {
      if (exportDisabled.value) return
      if (originalTitle === null) originalTitle = document.title
      document.title = reportBaseName()
      window.print()
    }
    onMounted(() => window.addEventListener('afterprint', restoreTitle))
    onBeforeUnmount(() => {
      window.removeEventListener('afterprint', restoreTitle)
      restoreTitle()
    })

    const exportCsv = () => {
      if (exportDisabled.value) return
      const quarterlyHeaders = [
        t('reports.quarterly.quarter'),
        t('reports.quarterly.totalOrders'),
        t('reports.quarterly.totalRevenue'),
        t('reports.quarterly.avgOrderValue'),
        t('reports.export.fulfillmentRatePct'),
      ]
      const monthlyHeaders = [
        t('reports.mom.month'),
        t('reports.mom.orders'),
        t('reports.mom.revenue'),
        t('reports.mom.change'),
        t('reports.export.growthPct'),
      ]
      const quarterlyRows = quarterlyData.value.map((q) => [
        q.quarter,
        q.total_orders,
        q.total_revenue,
        q.avg_order_value,
        q.fulfillment_rate,
      ])
      // First month has no previous value: change/growth are null -> empty cells
      const monthlyCsvRows = monthlyRows.value.map((r) => [
        r.month,
        r.order_count,
        r.revenue,
        r.hasPrevious ? r.changeValue : null,
        r.hasPrevious ? r.growthValue : null,
      ])
      const exp = (k) => t('reports.export.' + k)
      const text = [
        toCsvLine([t('reports.title')]),
        toCsvLine([exp('filters'), ...filterSummary.value.map((f) => `${f.label}: ${f.value}`)]),
        '',
        toCsvLine([t('reports.quarterly.title')]),
        buildCsv(quarterlyHeaders, quarterlyRows),
        '',
        toCsvLine([exp('monthlyTrends')]),
        buildCsv(monthlyHeaders, monthlyCsvRows),
      ].join('\r\n')
      downloadCsv(`${reportBaseName()}.csv`, text)
    }

    return {
      t,
      exportDisabled,
      exportCsv,
      exportPdf,
      filterSummary,
      currentCurrency,
      loading,
      error,
      loaded,
      reload,
      quarterlyData,
      monthlyRows,
      totalRevenue,
      avgMonthlyRevenue,
      totalOrders,
      bestQuarter,
      getBarHeight,
      getFulfillmentClass,
      formatCurrency,
    }
  },
}
</script>

<style scoped>
.reports {
  padding: 0;
}

.export-actions {
  display: flex;
  gap: var(--space-2);
}

.print-header h1 {
  margin: 0 0 var(--space-2);
}

.print-filter {
  margin-right: var(--space-4);
}

.chart-container {
  padding: var(--space-8) var(--space-4);
  min-height: 300px;
}

.bar-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 250px;
  gap: var(--space-2);
}

.bar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  min-width: 0;
  max-width: 80px;
}

.bar-container {
  height: 200px;
  display: flex;
  align-items: flex-end;
  width: 100%;
}

.bar {
  width: 100%;
  background: var(--info);
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  transition: all 0.3s;
  cursor: pointer;
}

.bar:hover {
  background: var(--info);
}

.bar-label {
  margin-top: var(--space-2);
  font-size: var(--text-xs);
  color: var(--text-muted);
  text-align: center;
  transform: rotate(-45deg);
  white-space: nowrap;
  margin-top: var(--space-6);
}

.positive-change {
  color: var(--success-ink);
  font-weight: 600;
}

.negative-change {
  color: var(--danger);
  font-weight: 600;
}

.empty-state {
  text-align: center;
  padding: var(--space-12);
  color: var(--text-muted);
}
</style>
