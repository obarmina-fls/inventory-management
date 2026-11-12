import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import './styles/tokens.css'
import './styles/base.css'
import { useTheme } from './composables/useTheme'
import App from './App.vue'
import Dashboard from './views/Dashboard.vue'
import Inventory from './views/Inventory.vue'
import Orders from './views/Orders.vue'
import Demand from './views/Demand.vue'
import Restocking from './views/Restocking.vue'
import Spending from './views/Spending.vue'
import Reports from './views/Reports.vue'

// Which global filters each route honours (route.meta.filters), read by FilterBar.
// Keep in sync with what each view actually sends to the API / applies client-side.
const ALL_FILTERS = ['period', 'location', 'category', 'status']

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Dashboard, meta: { filters: ALL_FILTERS } },
    // Inventory has no time dimension and no order status
    { path: '/inventory', component: Inventory, meta: { filters: ['location', 'category'] } },
    { path: '/orders', component: Orders, meta: { filters: ALL_FILTERS } },
    { path: '/demand', component: Demand, meta: { filters: ['location', 'category'] } },
    { path: '/restocking', component: Restocking, meta: { filters: [] } },
    // Costs (/api/spending/*) have no warehouse/category/status dimension, so revenue is kept
    // period-only too; that keeps Net Profit and Margin on a single scope.
    { path: '/spending', component: Spending, meta: { filters: ['period'] } },
    { path: '/reports', component: Reports, meta: { filters: ALL_FILTERS } },
  ],
})

// Apply saved/system theme before mount to avoid a light flash
useTheme()

const app = createApp(App)
app.use(router)
app.mount('#app')
