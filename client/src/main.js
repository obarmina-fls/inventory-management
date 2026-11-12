import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import './styles/tokens.css'
import './styles/base.css'
import { useTheme } from './composables/useTheme'
import { i18nReady } from './composables/useI18n'
import App from './App.vue'

// Which global filters each route honours (route.meta.filters), read by FilterBar.
// Keep in sync with what each view actually sends to the API / applies client-side.
const ALL_FILTERS = ['period', 'location', 'category', 'status']

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: () => import('./views/Dashboard.vue'), meta: { filters: ALL_FILTERS } },
    // Inventory has no time dimension and no order status
    {
      path: '/inventory',
      component: () => import('./views/Inventory.vue'),
      meta: { filters: ['location', 'category'] },
    },
    { path: '/orders', component: () => import('./views/Orders.vue'), meta: { filters: ALL_FILTERS } },
    { path: '/demand', component: () => import('./views/Demand.vue'), meta: { filters: ['location', 'category'] } },
    { path: '/restocking', component: () => import('./views/Restocking.vue'), meta: { filters: [] } },
    // Costs (/api/spending/*) have no warehouse/category/status dimension, so revenue is kept
    // period-only too; that keeps Net Profit and Margin on a single scope.
    { path: '/spending', component: () => import('./views/Spending.vue'), meta: { filters: ['period'] } },
    { path: '/reports', component: () => import('./views/Reports.vue'), meta: { filters: ALL_FILTERS } },
  ],
})

// Apply saved/system theme before mount to avoid a light flash
useTheme()

// Wait for the saved locale chunk so the first paint is already translated
i18nReady.finally(() => {
  const app = createApp(App)
  app.use(router)
  app.mount('#app')
})
