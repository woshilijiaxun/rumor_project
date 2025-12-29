<template>
  <div class="users-page">
    <div class="page-header">
      <h3>用户列表</h3>
      <button @click="fetchUsers" class="refresh-btn">刷新</button>
    </div>
    <div v-if="loading" class="loading">加载中...</div>
    <div v-if="error" class="error">{{ error }}</div>
    <table v-if="!loading && !error" class="users-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>用户名</th>
          <th>邮箱</th>
          <th>注册时间</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="user in users" :key="user.id">
          <td>{{ user.id }}</td>
          <td>{{ user.username }}</td>
          <td>{{ user.email || '-' }}</td>
          <td>{{ formatDateMs(user.created_at_ms) || formatDate(user.created_at) }}</td>
        </tr>
        <tr v-if="users.length === 0">
          <td colspan="4" class="empty">暂无用户数据</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import axios from 'axios'
export default {
  name: 'UsersPage',
  data() {
    return { users: [], loading: false, error: '' }
  },
  methods: {
    fetchUsers() {
      this.loading = true
      this.error = ''
      axios.get('/api/users')
        .then(response => {
          const rows = Array.isArray(response.data) ? response.data : response.data?.data
          if (Array.isArray(rows)) this.users = rows
          else if (response.data?.status === 'success' && Array.isArray(response.data?.data)) this.users = response.data.data
          else this.error = '返回数据格式不符合预期'
        })
        .catch(error => { this.error = '获取用户列表失败: ' + (error.response?.data?.message || error.message) })
        .finally(() => { this.loading = false })
    },
    formatDate(v) { if (!v) return '-'; const t = Date.parse(v); if (isNaN(t)) return v; return new Date(t).toLocaleString('zh-CN') },
    formatDateMs(ms) { if (ms == null) return '-'; const d = new Date(Number(ms)); if (isNaN(d.getTime())) return '-'; return d.toLocaleString('zh-CN') }
  },
  mounted() { this.fetchUsers() }
}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h3 { margin: 0; color: #333; }
.refresh-btn { padding: 8px 16px; background: #1890ff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
.refresh-btn:hover { background: #40a9ff; }
.loading, .error { text-align: left; padding: 8px 0; color: #666; }
.error { color: #d32f2f; }
.users-table { width: 100%; border-collapse: collapse; }
.users-table th, .users-table td { padding: 12px; text-align: left; border-bottom: 1px solid #f0f0f0; }
.users-table th { background: #fafafa; font-weight: 600; color: #333; }
.users-table tbody tr:hover { background: #fafafa; }
.empty { text-align: center; color: #999; padding: 40px; }
</style>

