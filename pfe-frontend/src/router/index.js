import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '../auth/useAuth'

import Login           from '../views/Login.vue'
import SearchCompany   from '../views/SearchCompany.vue'
import Recommendations from '../views/Recommendations.vue'
import Reports         from '../views/Reports.vue'
import Settings        from '../views/Settings.vue'

const routes = [
  { path: '/',                redirect: '/login' },
  { path: '/login',           component: Login,           meta: { public: true } },
  { path: '/search',          component: SearchCompany },
  { path: '/recommendations', component: Recommendations },
  { path: '/reports',         component: Reports },
  { path: '/settings',        component: Settings },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  const { isAuthenticated } = useAuth()

  // Already logged in → skip the login page
  if (to.meta.public && isAuthenticated.value) return '/search'

  // Protected route → redirect to custom login page
  if (!to.meta.public && !isAuthenticated.value) return '/login'

  return true
})

export default router
