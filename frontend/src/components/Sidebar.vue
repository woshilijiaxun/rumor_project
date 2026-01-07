<template>
  <nav class="sidebar-nav">
    <ul>
      <li :class="{ active: isActive('/dashboard') }" @click="go('/dashboard')">首页</li>
      <li v-if="isAdmin" :class="{ active: isActive('/users') }" @click="go('/users')">用户管理</li>
      <li :class="{ active: isActive('/algorithms') }" @click="go('/algorithms')">算法管理</li>
      <li :class="{ active: isActive('/files') }" @click="go('/files')">文件管理</li>
      <li :class="{ active: isActive('/identification') }" @click="go('/identification')">识别计算</li>
      <li :class="{ active: isActive('/settings') }" @click="go('/settings')">系统设置</li>
      <li v-if="isAdmin" :class="{ active: isActive('/admin-settings') }" @click="go('/admin-settings')">管理员设置</li>
    </ul>
  </nav>
</template>

<script>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

export default {
  name: 'Sidebar',
  setup() {
    const route = useRoute()
    const router = useRouter()

    const go = (path) => {
      if (route.path !== path) router.push(path)
    }
    const isActive = (path) => route.path.startsWith(path)

    const isAdmin = computed(() => {
      try {
        const raw = localStorage.getItem('user')
        const u = raw ? JSON.parse(raw) : null
        return (u && u.role === 'admin')
      } catch (e) {
        return false
      }
    })

    return { go, isActive, isAdmin }
  }
}
</script>

<style scoped>
.sidebar-nav { display: flex; flex-direction: column; height: 100%; }
.sidebar-nav ul { list-style: none; padding: 0; margin: 0; }
.sidebar-nav li { padding: 15px 20px; cursor: pointer; user-select: none; transition: background-color 0.3s; display: flex; align-items: center; line-height: 1; }
.sidebar-nav li:hover { background-color: #f5f7fa; }
.sidebar-nav li.active { background-color: #e6f4ff; color: #1677ff; }
</style>
