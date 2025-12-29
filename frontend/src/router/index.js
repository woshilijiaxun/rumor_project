import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import AdminLayout from '../layouts/AdminLayout.vue'
import Dashboard from '../modules/dashboard/Dashboard.vue'
import UsersPage from '../modules/users/UsersPage.vue'
import AlgorithmsPage from '../modules/algorithms/AlgorithmsPage.vue'
import FilesPage from '../modules/files/FilesPage.vue'
import SettingsPage from '../modules/settings/SettingsPage.vue'
import IdentificationPage from '../modules/identification/IdentificationPage.vue'

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
      { path: 'users', component: UsersPage },
      { path: 'algorithms', component: AlgorithmsPage },
      { path: 'files', component: FilesPage },
      { path: 'identification', component: IdentificationPage },
      { path: 'settings', component: SettingsPage },
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

router.beforeEach((to, from, next) => {
  const token = (typeof window !== 'undefined') ? localStorage.getItem('token') : null
  if (to.matched.some(r => r.meta && r.meta.requiresAuth) && !token) {
    const redirect = encodeURIComponent(to.fullPath || '/dashboard')
    next({ path: '/login', query: { redirect } })
  } else if ((to.path === '/login' || to.path === '/register') && token) {
    const target = to.query.redirect ? decodeURIComponent(to.query.redirect) : '/dashboard'
    next(target)
  } else {
    next()
  }
})

export default router
