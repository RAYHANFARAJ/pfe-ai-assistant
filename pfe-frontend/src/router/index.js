import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '../auth/useAuth'

import Login            from '../views/Login.vue'
import SearchCompany    from '../views/SearchCompany.vue'
import CampaignScoring  from '../views/CampaignScoring.vue'
import Recommendations  from '../views/Recommendations.vue'
import Reports          from '../views/Reports.vue'
import Settings         from '../views/Settings.vue'
import AdminDashboard   from '../views/admin/AdminDashboard.vue'
import ProductDetail    from '../views/admin/ProductDetail.vue'

const routes = [
  { path: '/',                redirect: '/login' },
  { path: '/login',           component: Login,           meta: { public: true } },
  { path: '/search',          component: SearchCompany },
  { path: '/campaigns',       component: CampaignScoring },
  { path: '/recommendations', component: Recommendations },
  { path: '/reports',         component: Reports },
  { path: '/settings',        component: Settings },
  { path: '/admin',                    component: AdminDashboard, meta: { requiresAdmin: true } },
  { path: '/admin/products/:id',       component: ProductDetail,  meta: { requiresAdmin: true } },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  const { isAuthenticated, hasRole } = useAuth()

  if (to.meta.public && isAuthenticated.value) return '/search'
  if (!to.meta.public && !isAuthenticated.value) return '/login'
  if (to.meta.requiresAdmin && !hasRole('admin')) return '/search'

  return true
})

export default router
