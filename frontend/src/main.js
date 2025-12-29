import { createApp } from 'vue'
import App from './App.vue'   // 应该是 App.vue
import router from './router'
import axios from 'axios'

// Axios 全局鉴权拦截器
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

axios.interceptors.response.use(
  (resp) => resp,
  (error) => {
    if (error?.response?.status === 401) {
      // 未授权/过期，清理并跳转登录
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      const redirect = encodeURIComponent(window.location.pathname + window.location.search)
      router.push({ path: '/login', query: { redirect } })
    }
    return Promise.reject(error)
  }
)

createApp(App).use(router).mount('#app')
