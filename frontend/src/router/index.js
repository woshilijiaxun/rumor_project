import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import AdminLayout from '../layouts/AdminLayout.vue'
import Dashboard from '../modules/dashboard/Dashboard.vue'
import UsersPage from '../modules/users/UsersPage.vue'
import AlgorithmsPage from '../modules/algorithms/AlgorithmsPage.vue'
import FilesPage from '../modules/files/FilesPage.vue'
import SettingsPage from '../modules/settings/SettingsPage.vue'
import AdminSettingsPage from '../modules/admin/AdminSettingsPage.vue'
import IdentificationPage from '../modules/identification/IdentificationPage.vue'
import IdentificationHistoryDetailPage from '../modules/identification/IdentificationHistoryDetailPage.vue'
import IdentificationReportPage from '../modules/identification/IdentificationReportPage.vue'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: Login },
  { path: '/register', component: Register },
  {
    path: '/',
    component: AdminLayout,
    meta: { requiresAuth: true },
    children: [
      { path: 'dashboard', component: Dashboard },
      { path: 'users', component: UsersPage, meta: { requiresAdmin: true } },
      { path: 'algorithms', component: AlgorithmsPage },
      { path: 'files', component: FilesPage },
      { path: 'identification', component: IdentificationPage },
      { path: 'identification/history/:taskId', component: IdentificationHistoryDetailPage },
      { path: 'identification/report/:taskId', component: IdentificationReportPage },
      { path: 'settings', component: SettingsPage },
      { path: 'admin-settings', component: AdminSettingsPage, meta: { requiresAdmin: true } },
      { path: 'home', redirect: '/dashboard' },
      { path: '', redirect: '/dashboard' }
    ]
  },
  { path: '/home', redirect: '/dashboard' },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

function getUserRole() {
  try {
    const raw = localStorage.getItem('user')
    if (!raw) return 'user'
    const u = JSON.parse(raw)
    return u?.role || 'user'
  } catch (e) {
    return 'user'
  }
}

router.beforeEach((to, _from, next) => {
  const token = (typeof window !== 'undefined') ? localStorage.getItem('token') : null

  // 1) 需要登录但没 token
  if (to.matched.some(r => r.meta && r.meta.requiresAuth) && !token) {
    const redirect = encodeURIComponent(to.fullPath || '/dashboard')
    next({ path: '/login', query: { redirect } })
    return
  }

  // 2) 登录后访问登录/注册页 -> 跳转
  if ((to.path === '/login' || to.path === '/register') && token) {
    const target = to.query.redirect ? decodeURIComponent(to.query.redirect) : '/dashboard'
    next(target)
    return
  }

  // 3) 管理员路由保护
  if (to.matched.some(r => r.meta && r.meta.requiresAdmin)) {
    const role = getUserRole()
    if (role !== 'admin') {
      next('/dashboard')
      return
    }
  }

  next()
})

export default router
