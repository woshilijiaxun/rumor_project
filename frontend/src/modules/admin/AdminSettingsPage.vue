<template>
  <div class="admin-settings-page">
    <div class="page-header">
      <h2>管理员设置</h2>
      <p class="subtitle">系统级配置与审计，仅管理员可见。</p>
    </div>

    <!-- 系统配置 -->
    <section class="card">
      <button class="card-header" type="button" @click="toggle('config')">
        <span class="card-title">系统配置</span>
        <span class="chevron" :class="{ open: openMap.config }">▾</span>
      </button>

      <div v-show="openMap.config" class="card-body">
        <div v-if="loading.config" class="loading">加载中...</div>
        <form v-else @submit.prevent="saveConfig" class="config-form">
          <div class="form-group">
            <label class="form-label">最大上传大小 (MB)</label>
            <input 
              v-model.number="systemConfig.max_upload_mb" 
              type="number" 
              min="1" 
              class="form-control"
            >
          </div>
          
          <div class="form-group">
            <label class="form-label">最大边数限制</label>
            <input 
              v-model.number="systemConfig.max_edges_limit" 
              type="number" 
              min="100" 
              step="100"
              class="form-control"
            >
          </div>
          
          <div class="form-group">
            <label class="form-label">默认算法标识</label>
            <input 
              v-model="systemConfig.default_algorithm_key" 
              type="text" 
              class="form-control"
              placeholder="例如：graph_community_detection"
            >
          </div>
          
          
          <div class="form-actions">
            <button 
              type="submit" 
              class="btn btn-primary"
              :disabled="saving"
            >
              <span v-if="saving">保存中...</span>
              <span v-else>保存配置</span>
            </button>
            <span v-if="saveStatus.message" :class="['status', saveStatus.type]">
              {{ saveStatus.message }}
            </span>
          </div>
        </form>
      </div>
    </section>

    <!-- 算法启停 -->
    <section class="card">
      <button class="card-header" type="button" @click="toggle('algo')">
        <span class="card-title">算法启用 / 停用</span>
        <span class="chevron" :class="{ open: openMap.algo }">▾</span>
      </button>

      <div v-show="openMap.algo" class="card-body">
        <div class="algo-toolbar">
          <div class="field">
            <label class="label">搜索</label>
            <input v-model="algoSearch" class="input" placeholder="搜索算法名称 / algo_key" @keyup.enter="fetchAlgorithms" />
          </div>
          <div class="field-actions algo-actions">
            <button class="btn btn-success" type="button" @click="enableAll" :disabled="loading.algorithms || !hasInactive">
              一键启用
            </button>
            <button class="btn btn-danger" type="button" @click="disableAll" :disabled="loading.algorithms || !hasActive">
              一键停用
            </button>
            <button class="btn btn-info" type="button" @click="fetchAlgorithms" :disabled="loading.algorithms">
              <span v-if="loading.algorithms">加载中...</span>
              <span v-else>刷新</span>
            </button>
          </div>
        </div>

        <div v-if="algoError" class="status error" style="margin: 10px 0;">{{ algoError }}</div>

        <div class="table-wrap algo-table" style="margin-top: 10px;">
          <table class="table" style="min-width: 720px;">
            <thead>
              <tr>
                <th style="width: 44px;"></th>
                <th style="width: 260px;">名称</th>
                <th>algo_key</th>
                <th style="width: 160px;">描述</th>
                <th style="width: 120px;">状态</th>
                <th style="width: 150px;">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="loading.algorithms && algorithms.items.length === 0">
                <td colspan="5" class="empty">加载中...</td>
              </tr>
              <tr v-else-if="!loading.algorithms && algorithms.items.length === 0">
                <td colspan="5" class="empty">暂无算法</td>
              </tr>
              <tr v-else v-for="a in filteredAlgorithms" :key="a.id">
                <td class="algo-dot-cell">
                  <span class="dot" :class="(a.status === 'active') ? 'dot-ok' : 'dot-off'"></span>
                </td>
                <td class="algo-name">{{ a.name || '-' }}</td>
                <td class="mono algo-key">{{ a.algo_key || '-' }}</td>
                <td class="algo-desc">
                  <span
                    class="algo-desc-text"
                    @mouseenter="showAlgoTip(a.description, $event)"
                    @mouseleave="hideAlgoTip"
                  >
                    {{ a.description || '-' }}
                  </span>
                </td>
                <td>
                  <span class="tag" :class="(a.status === 'active') ? 'ok' : 'off'">
                    {{ (a.status === 'active') ? '启用' : '停用' }}
                  </span>
                </td>
                <td>
                  <button
                    class="btn btn-sm"
                    :class="(a.status === 'active') ? 'btn-danger' : 'btn-success'"
                    type="button"
                    @click="toggleAlgorithmStatus(a)"
                    :disabled="algoUpdatingId === a.id"
                  >
                    <span v-if="algoUpdatingId === a.id">处理中...</span>
                    <span v-else>{{ (a.status === 'active') ? '停用' : '启用' }}</span>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- 自定义 tooltip（算法描述） -->
    <div
      v-if="tooltip.show"
      class="algo-tooltip"
      :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px' }"
    >
      {{ tooltip.content }}
    </div>

    <!-- 审计日志 -->
    <section class="card">
      <button class="card-header" type="button" @click="toggle('audit')">
        <span class="card-title">审计日志</span>
        <span class="chevron" :class="{ open: openMap.audit }">▾</span>
      </button>

      <div v-show="openMap.audit" class="card-body">
        <div class="toolbar">
          <div class="field">
            <label class="label">Action</label>
            <select v-model="auditFilters.action" class="input">
              <option value="">全部</option>
              <option v-for="opt in auditActionOptions" :key="opt.value" :value="opt.value">
                {{ opt.label }}
              </option>
            </select>
          </div>
          <div class="field">
            <label class="label">关键词</label>
            <input 
              v-model="auditFilters.keyword" 
              class="input" 
              placeholder="搜索 target/detail 等"
              @keyup.enter="fetchAuditLogs"
            />
          </div>
          <div class="field field-actions">
            <button 
              class="btn btn-primary" 
              type="button" 
              @click="fetchAuditLogs(true)"
              :disabled="loading.audit"
            >
              <span v-if="loading.audit">查询中...</span>
              <span v-else>查询</span>
            </button>
            <button
              class="btn btn-secondary"
              type="button"
              @click="resetAuditFilters"
              :disabled="loading.audit || loading.export"
            >
              重置
            </button>
            <button
              class="btn btn-secondary"
              type="button"
              @click="exportAuditLogs('csv')"
              :disabled="loading.audit || loading.export"
            >
              <span v-if="loading.export && exportType === 'csv'">导出中...</span>
              <span v-else>导出 CSV</span>
            </button>
            <button
              class="btn btn-secondary"
              type="button"
              @click="exportAuditLogs('excel')"
              :disabled="loading.audit || loading.export"
            >
              <span v-if="loading.export && exportType === 'excel'">导出中...</span>
              <span v-else>导出 Excel</span>
            </button>
          </div>
        </div>

        <div class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th style="width: 160px;">时间</th>
                <th style="width: 100px;">操作者</th>
                <th style="width: 140px;">action</th>
                <th style="width: 150px;">target</th>
                <th>详情</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="loading.audit && auditLogs.items.length === 0">
                <td colspan="5" class="empty">加载中...</td>
              </tr>
              <tr v-else-if="auditLogs.items.length === 0">
                <td colspan="5" class="empty">暂无数据</td>
              </tr>
              <tr v-else v-for="row in auditLogs.items" :key="row.id">
                <td class="mono">{{ formatDateTime(row.created_at) }}</td>
                <td class="mono">{{ row.actor_user_id || '系统' }}</td>
                <td class="mono">{{ formatAction(row.action) }}</td>
                <td class="mono">
                  {{ row.target_type || '' }}
                  <template v-if="row.target_id">/{{ row.target_id }}</template>
                </td>
                <td>
                  <div class="detail-cell">
                    <div class="detail-summary-text">{{ summarizeDetail(row) }}</div>
                    <details v-if="row.detail_json || row.detail">
                      <summary class="details-summary">查看原始 JSON</summary>
                      <pre class="json">{{ formatJson(row.detail_json ?? row.detail) }}</pre>
                    </details>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="pager">
          <button 
            class="btn btn-secondary" 
            type="button" 
            @click="changePage(auditLogs.page - 1)"
            :disabled="auditLogs.page <= 1 || loading.audit"
          >
            上一页
          </button>
          <div class="pager-info">
            第 {{ auditLogs.page }} 页 / 共 {{ auditLogs.total_pages || 1 }} 页
            <span class="total">(共 {{ auditLogs.total }} 条)</span>
          </div>
          <button 
            class="btn btn-secondary" 
            type="button" 
            @click="changePage(auditLogs.page + 1)"
            :disabled="auditLogs.page >= auditLogs.total_pages || loading.audit"
          >
            下一页
          </button>
        </div>
      </div>
    </section>

    <!-- 健康检查（保留占位） -->
    <section class="card">
      <button class="card-header" type="button" @click="toggle('health')">
        <span class="card-title">系统健康检查</span>
        <span class="chevron" :class="{ open: openMap.health }">▾</span>
      </button>

      <div v-show="openMap.health" class="card-body">
        <p class="hint">即将支持：/health、数据库连接、磁盘空间等（展示即可）。</p>
        <button class="btn btn-secondary" disabled>刷新状态（待后端接口）</button>
      </div>
    </section>
  </div>
</template>

<script>
import { computed, reactive, ref } from 'vue'
import axios from 'axios'

export default {
  name: 'AdminSettingsPage',
  setup() {
    const openMap = reactive({
      config: false,
      algo: false,
      audit: false,
      health: false
    })

    const toggle = (k) => {
      openMap[k] = !openMap[k]
      if (openMap[k]) {
        if (k === 'audit' && !auditLogsInitialized.value) {
          fetchAuditLogs(true)
          auditLogsInitialized.value = true
        } else if (k === 'config' && !configInitialized.value) {
          fetchSystemConfig()
          configInitialized.value = true
        } else if (k === 'algo' && !algorithmsInitialized.value) {
          fetchAlgorithms()
          algorithmsInitialized.value = true
        }
      }
    }

    // 审计日志
    const auditLogsInitialized = ref(false)
    const auditFilters = reactive({
      action: '',
      keyword: ''
    })

    const auditLogs = reactive({
      items: [],
      page: 1,
      page_size: 20,
      total: 0,
      total_pages: 0
    })

    const loading = reactive({
      audit: false,
      config: false,
      export: false,
      algorithms: false
    })

    const exportType = ref('')

    const exportAuditLogs = async (type) => {
      if (loading.export) return
      exportType.value = type
      loading.export = true

      try {
        const params = {
          type: type === 'excel' ? 'excel' : 'csv',
          ...(auditFilters.action && { action: auditFilters.action }),
          ...(auditFilters.keyword && { keyword: auditFilters.keyword })
        }

        // 用原始 axios 请求以支持 blob 下载
        const res = await axios.get('/api/admin/audit-logs/export', {
          params,
          responseType: 'blob'
        })

        // 后端报错时可能仍是 blob（json），这里尝试解析
        const contentType = res?.headers?.['content-type'] || ''
        if (contentType.includes('application/json')) {
          const text = await res.data.text()
          let msg = text
          try {
            const obj = JSON.parse(text)
            msg = obj?.message || obj?.msg || text
          } catch (e) {
            // ignore
          }
          throw new Error(msg)
        }

        const blob = new Blob([res.data], { type: contentType || (type === 'excel'
          ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
          : 'text/csv; charset=utf-8') })

        const ts = new Date()
        const pad = (n) => String(n).padStart(2, '0')
        const stamp = `${ts.getFullYear()}${pad(ts.getMonth() + 1)}${pad(ts.getDate())}_${pad(ts.getHours())}${pad(ts.getMinutes())}${pad(ts.getSeconds())}`
        const filename = type === 'excel' ? `audit_logs_${stamp}.xlsx` : `audit_logs_${stamp}.csv`

        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = filename
        document.body.appendChild(a)
        a.click()
        a.remove()
        window.URL.revokeObjectURL(url)
      } catch (error) {
        console.error('导出审计日志失败:', error)
        alert('导出失败：' + (error.response?.data?.message || error.message || '未知错误'))
      } finally {
        loading.export = false
        exportType.value = ''
      }
    }

    const fetchAuditLogs = async (resetPage = false) => {
      if (resetPage) auditLogs.page = 1
      loading.audit = true
      try {
        const params = {
          page: auditLogs.page,
          page_size: auditLogs.page_size,
          ...(auditFilters.action && { action: auditFilters.action }),
          ...(auditFilters.keyword && { keyword: auditFilters.keyword })
        }

        const res = await axios.get('/api/admin/audit-logs', { params })
        if (res && res.data && res.data.data) {
          Object.assign(auditLogs, res.data.data)
        }
      } catch (error) {
        console.error('获取审计日志失败:', error)
        if (error.response && error.response.data) {
          console.error('错误详情:', error.response.data)
        }
      } finally {
        loading.audit = false
      }
    }

    const resetAuditFilters = () => {
      auditFilters.action = ''
      auditFilters.keyword = ''
      fetchAuditLogs(true)
    }

    const changePage = (newPage) => {
      if (newPage < 1 || (auditLogs.total_pages && newPage > auditLogs.total_pages)) {
        return
      }
      auditLogs.page = newPage
      fetchAuditLogs()
    }

    // 算法启停
    const algorithmsInitialized = ref(false)
    const algoSearch = ref('')
    const algoError = ref('')
    const algoUpdatingId = ref(null)
    const algorithms = reactive({
      items: [],
      page: 1,
      page_size: 200,
      total: 0,
      total_pages: 0
    })

    const filteredAlgorithms = computed(() => {
      const kw = (algoSearch.value || '').trim().toLowerCase()
      const arr = Array.isArray(algorithms.items) ? algorithms.items : []
      if (!kw) return arr
      return arr.filter(a => {
        const name = String(a?.name || '').toLowerCase()
        const key = String(a?.algo_key || '').toLowerCase()
        return name.includes(kw) || key.includes(kw)
      })
    })

    const fetchAlgorithms = async () => {
      loading.algorithms = true
      algoError.value = ''
      try {
        const res = await axios.get('/api/algorithms', { params: { page: 1, page_size: algorithms.page_size } })
        const d = res?.data
        const items = d?.data?.items
        if (d?.status === 'success' && Array.isArray(items)) {
          algorithms.items = items
          algorithms.total = d?.data?.total ?? items.length
          algorithms.page = d?.data?.page ?? 1
          algorithms.page_size = d?.data?.page_size ?? algorithms.page_size
          algorithms.total_pages = d?.data?.total_pages ?? 1
        } else {
          algorithms.items = []
          algoError.value = d?.message || '获取算法列表失败（返回格式不符合预期）'
        }
      } catch (e) {
        algorithms.items = []
        algoError.value = e?.response?.data?.message || e?.message || '获取算法列表失败'
      } finally {
        loading.algorithms = false
      }
    }

    const hasActive = computed(() => algorithms.items.some(a => a.status === 'active'))
    const hasInactive = computed(() => algorithms.items.some(a => a.status !== 'active'))

    const updateAlgorithmStatus = async (algorithm, status) => {
      if (!algorithm || !algorithm.id) return

      const originalStatus = algorithm.status
      algoUpdatingId.value = algorithm.id
      try {
        // 乐观更新
        algorithm.status = status

        const res = await axios.put(`/api/algorithms/${algorithm.id}`, { status })
        if (res?.data?.status !== 'success') {
          throw new Error(res?.data?.message || '更新失败')
        }
        return true
      } catch (error) {
        // 回滚状态
        algorithm.status = originalStatus
        console.error('更新算法状态失败:', error)
        throw error
      } finally {
        if (algoUpdatingId.value === algorithm.id) {
          algoUpdatingId.value = null
        }
      }
    }

    const toggleAlgorithmStatus = async (algorithm) => {
      if (!algorithm) return
      const nextStatus = algorithm.status === 'active' ? 'inactive' : 'active'
      const action = nextStatus === 'active' ? '启用' : '停用'
      if (!confirm(`确定要${action}算法 "${algorithm.name || algorithm.algo_key}" 吗？`)) {
        return
      }

      try {
        await updateAlgorithmStatus(algorithm, nextStatus)
      } catch (error) {
        alert(`${action}失败: ${error.response?.data?.message || error.message || '未知错误'}`)
      }
    }

    const batchUpdateStatus = async (status) => {
      const targetAlgorithms = filteredAlgorithms.value.filter(a => a.status !== status)
      if (targetAlgorithms.length === 0) {
        alert('没有需要更新的算法。')
        return
      }

      const action = status === 'active' ? '启用' : '停用'
      const confirmMessage = `确定要${action}所有可见的 ${targetAlgorithms.length} 个算法吗？`

      if (!confirm(confirmMessage)) {
        return
      }

      const promises = targetAlgorithms.map(a => updateAlgorithmStatus(a, status))
      const results = await Promise.allSettled(promises)

      const failed = results.filter(r => r.status === 'rejected')
      if (failed.length > 0) {
        console.error('部分算法更新失败:', failed)
        alert(`有 ${failed.length} 个算法${action}失败，请检查控制台获取详情。`)
      } else {
        alert(`已成功${action} ${targetAlgorithms.length} 个算法。`)
      }
    }

    const enableAll = () => batchUpdateStatus('active')
    const disableAll = () => batchUpdateStatus('inactive')

    // 自定义 tooltip 相关
    const tooltip = reactive({
      show: false,
      content: '',
      x: 0,
      y: 0
    })

    const showAlgoTip = (content, event) => {
      if (!content) return
      
      tooltip.content = content
      tooltip.show = true
      
      // 设置位置（鼠标右下方）
      const offset = 10
      tooltip.x = event.pageX + offset
      tooltip.y = event.pageY + offset
    }

    const hideAlgoTip = () => {
      tooltip.show = false
    }

    // 系统配置
    const configInitialized = ref(false)
    const systemConfig = reactive({
      max_upload_mb: '20',
      max_edges_limit: '10000',
      default_algorithm_key: '',
      enable_network_visualization: '1',
      enable_debunk_module: '1'
    })

    const saving = ref(false)
    const saveStatus = reactive({
      type: '', // 'success' or 'error'
      message: ''
    })

    const fetchSystemConfig = async () => {
      loading.config = true
      try {
        const res = await axios.get('/api/admin/config')
        if (res && res.data && res.data.data) {
          // 只更新已有的配置项，避免覆盖默认值
          Object.keys(systemConfig).forEach(key => {
            if (res.data.data[key] !== undefined) {
              systemConfig[key] = res.data.data[key]
            }
          })
        }
      } catch (error) {
        console.error('获取系统配置失败:', error)
      } finally {
        loading.config = false
      }
    }

    const saveConfig = async () => {
      saving.value = true
      saveStatus.type = ''
      saveStatus.message = ''
      
      try {
        // 准备要保存的配置，只包含有变化的字段
        const configToSave = {}
        const defaultConfig = {
          max_upload_mb: '20',
          max_edges_limit: '10000',
          default_algorithm_key: '',
          enable_network_visualization: '1',
          enable_debunk_module: '1'
        }
        
        // 只收集与默认值不同的配置项
        Object.keys(systemConfig).forEach(key => {
          if (systemConfig[key] !== defaultConfig[key]) {
            configToSave[key] = systemConfig[key]
          }
        })
        
        const res = await axios.post('/api/admin/config', configToSave)

        if (res && res.data && res.data.status === 'success') {
          saveStatus.type = 'success'
          saveStatus.message = res.data.message || '配置保存成功'

          // 3秒后清除成功消息
          setTimeout(() => {
            if (saveStatus.type === 'success') {
              saveStatus.message = ''
            }
          }, 3000)

          // 重新加载配置，确保与服务器同步
          fetchSystemConfig()
        } else {
          throw new Error(res?.data?.message || '保存失败')
        }
      } catch (error) {
        console.error('保存配置失败:', error)
        saveStatus.type = 'error'
        saveStatus.message = '保存失败: ' + (error.response?.data?.message || error.message || '未知错误')
      } finally {
        saving.value = false
      }
    }

    // 工具函数
    const formatDateTime = (dateTimeStr) => {
      if (!dateTimeStr) return ''
      const date = new Date(dateTimeStr)
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      }).replace(/\//g, '-')
    }

    const formatJson = (obj) => {
      try {
        if (typeof obj === 'string') {
          return JSON.stringify(JSON.parse(obj), null, 2)
        }
        return JSON.stringify(obj, null, 2)
      } catch (e) {
        return String(obj)
      }
    }

    const auditActionOptions = [
      { value: 'FILE_UPLOAD', label: '文件上传' },
      { value: 'FILE_DELETE', label: '文件删除' },
      { value: 'TASK_CREATE', label: '创建识别任务' },
      { value: 'TASK_CANCEL', label: '取消识别任务' },
      { value: 'TASK_STATUS_CHANGE', label: '任务状态变更' },
      { value: 'CONFIG_UPDATE', label: '更新系统配置' },
      { value: 'ALGORITHM_CREATE', label: '创建算法' },
      { value: 'ALGORITHM_DELETE', label: '删除算法' },
      { value: 'ALGORITHM_STATUS_UPDATE', label: '算法启停/状态变更' },
      { value: 'LOGIN_SUCCESS', label: '登录成功' },
      { value: 'LOGIN_FAIL', label: '登录失败' },
      { value: 'REGISTER', label: '用户注册' }
    ]

    const formatAction = (action) => {
      const map = {
        FILE_UPLOAD: '文件上传',
        FILE_DELETE: '文件删除',
        TASK_CREATE: '创建识别任务',
        TASK_CANCEL: '取消识别任务',
        TASK_STATUS_CHANGE: '任务状态变更',
        CONFIG_UPDATE: '更新系统配置',
        ALGORITHM_CREATE: '创建算法',
        ALGORITHM_DELETE: '删除算法',
        ALGORITHM_STATUS_UPDATE: '算法启停/状态变更',
        LOGIN_SUCCESS: '登录成功',
        LOGIN_FAIL: '登录失败',
        REGISTER: '用户注册'
      }
      return map[action] || action
    }

    const summarizeDetail = (row) => {
      const raw = row?.detail_json ?? row?.detail
      if (raw === null || raw === undefined || raw === '') return ''

      let d
      try {
        d = (typeof raw === 'string') ? JSON.parse(raw) : raw
      } catch (e) {
        return String(raw)
      }

      const parts = []
      const result = d?.result
      if (result === 'success') parts.push('结果：成功')
      else if (result === 'fail') parts.push('结果：失败')

      if (d?.error) parts.push(`错误：${String(d.error).slice(0, 120)}`)

      // 通用 extra
      const ex = d?.extra || {}
      if (ex.original_name) parts.push(`文件：${ex.original_name}`)
      if (ex.file_id) parts.push(`file_id=${ex.file_id}`)
      if (ex.algorithm_key) parts.push(`algo=${ex.algorithm_key}`)
      if (ex.status) parts.push(`status=${ex.status}`)

      // request
      const req = d?.request || {}
      if (req.file_id) parts.push(`file_id=${req.file_id}`)
      if (req.algorithm_key) parts.push(`algo=${req.algorithm_key}`)
      if (req.visibility) parts.push(`visibility=${req.visibility}`)

      // 配置变更
      if (Array.isArray(d?.updated_keys) && d.updated_keys.length) {
        parts.push(`更新项：${d.updated_keys.join(',')}`)
      }

      // target
      if (row?.target_type) {
        const tid = row?.target_id ? `/${row.target_id}` : ''
        parts.push(`target=${row.target_type}${tid}`)
      }

      return parts.join(' | ')
    }

    return {
      openMap,
      toggle,
      // 审计日志
      auditFilters,
      auditLogs,
      fetchAuditLogs,
      changePage,
      loading,
      exportAuditLogs,
      exportType,
      // 系统配置
      systemConfig,
      saveConfig,
      saving,
      saveStatus,
      // 工具函数
      formatDateTime,
      formatJson,
      formatAction,
      auditActionOptions,
      summarizeDetail,
      resetAuditFilters,
      // 算法启停
      algorithms,
      algoSearch,
      algoError,
      algoUpdatingId,
      filteredAlgorithms,
      fetchAlgorithms,
      toggleAlgorithmStatus,
      hasActive,
      hasInactive,
      enableAll,
      disableAll,
      tooltip,
      showAlgoTip,
      hideAlgoTip
    }
  }
}
</script>

<style scoped>
.page-header {
  margin-bottom: 16px;
}

.page-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 800;
  color: #111827;
}

.subtitle {
  margin: 6px 0 0;
  font-size: 12px;
  color: #6b7280;
}

.card {
  background: #fff;
  border-radius: 10px;
  padding: 16px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
  border: 1px solid #eef2ff;
  margin-bottom: 14px;
}

.card-header {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 2px 0 12px;
  border: none;
  background: transparent;
  cursor: pointer;
  user-select: none;
}

.card-title {
  font-size: 15px;
  font-weight: 800;
  color: #111827;
}

.chevron {
  font-size: 14px;
  color: #6b7280;
  transition: transform 0.18s ease;
  transform: rotate(-90deg);
}

.chevron.open {
  transform: rotate(0deg);
}

.card-body {
  padding-top: 8px;
}

.hint {
  margin: 0 0 10px;
  font-size: 12px;
  color: #6b7280;
  line-height: 1.6;
}

.loading {
  padding: 20px;
  text-align: center;
  color: #666;
}

/* 表单样式 */
.config-form {
  max-width: 600px;
}

.form-group {
  margin-bottom: 16px;
}

.form-label {
  display: block;
  margin-bottom: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #374151;
}

.form-control {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.form-control:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-check {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.form-check-input {
  margin-right: 8px;
}

.form-check-label {
  font-size: 13px;
  color: #374151;
}

.form-actions {
  margin-top: 24px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.status {
  font-size: 13px;
  padding: 4px 8px;
  border-radius: 4px;
}

.status.success {
  color: #065f46;
  background-color: #d1fae5;
}

.status.error {
  color: #991b1b;
  background-color: #fee2e2;
}

/* 工具栏（Web端）
   目标：筛选项一行，按钮组紧跟在同一行右侧，不要把整块高度撑高 */
.toolbar {
  display: grid;
  grid-template-columns: 240px 520px auto;
  justify-content: space-between;
  gap: 12px;
  align-items: end;
  margin-bottom: 16px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.field-actions {
  display: grid;
  grid-template-columns: repeat(2, max-content);
  gap: 8px;
  justify-content: end;
  align-items: center;
}

.field-actions .btn {
  white-space: nowrap;
}

.detail-cell {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.detail-summary-text {
  font-size: 12px;
  color: #374151;
  line-height: 1.4;
}

.label {
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
}

.input {
  height: 36px;
  padding: 0 10px;
  border-radius: 6px;
  border: 1px solid #d1d5db;
  font-size: 13px;
  min-width: 100%;
  transition: border-color 0.2s;
}

.input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* 表格样式 */
.table-wrap {
  overflow: auto;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  margin: 12px 0;
}

.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  min-width: 800px;
}

.table th,
.table td {
  padding: 10px 12px;
  border-bottom: 1px solid #f3f4f6;
  vertical-align: top;
  text-align: left;
}

.table th {
  color: #4b5563;
  background: #f9fafb;
  font-weight: 600;
  position: sticky;
  top: 0;
  z-index: 1;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.5;
}

.details-summary {
  cursor: pointer;
  color: #3b82f6;
  user-select: none;
  font-size: 12px;
  display: inline-block;
  padding: 2px 6px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.details-summary:hover {
  background-color: #f3f4f6;
}

.json {
  margin: 8px 0 0;
  padding: 10px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  overflow: auto;
  max-height: 300px;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  color: #334155;
}

.empty {
  text-align: center;
  color: #6b7280;
  padding: 20px;
  font-size: 13px;
}

/* 分页 */
.pager {
  margin-top: 16px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
}

.pager-info {
  font-size: 13px;
  color: #6b7280;
  margin: 0 8px;
}

.pager-info .total {
  color: #9ca3af;
  margin-left: 4px;
}

/* 按钮样式 */
.btn {
  padding: 8px 14px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  line-height: 1;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #e5e7eb;
}

.btn-secondary:hover:not(:disabled) {
  background: #e5e7eb;
}

.btn-primary {
  background: #3b82f6;
  color: white;
  border: 1px solid #2563eb;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

/* 语义化按钮（算法工具栏） */
.btn-success {
  background: #22c55e;
  color: #fff;
  border: 1px solid #16a34a;
}

.btn-success:hover:not(:disabled) {
  background: #16a34a;
}

.btn-danger {
  background: #ef4444;
  color: #fff;
  border: 1px solid #dc2626;
}

.btn-danger:hover:not(:disabled) {
  background: #dc2626;
}

.btn-info {
  background: #3b82f6;
  color: #fff;
  border: 1px solid #2563eb;
}

.btn-info:hover:not(:disabled) {
  background: #2563eb;
}

/* 算法启停样式增强 */
.algo-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: end;
  margin-bottom: 8px;
}

.algo-toolbar .field {
  flex: 1;
  min-width: 240px;
  max-width: 520px;
}

.algo-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-left: auto;
  justify-content: flex-end;
  align-items: center;
}

.algo-table {
  border-radius: 10px;
}

.algo-dot-cell {
  width: 44px;
  text-align: center;
}

.dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 999px;
}

.dot-ok {
  background: #10b981;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.18);
}

.dot-off {
  background: #ef4444;
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.16);
}

.algo-name {
  font-weight: 700;
  color: #111827;
}

.algo-key {
  color: #6b7280;
}

.algo-desc {
  max-width: 380px;
}

.algo-desc-text {
  display: inline-block;
  max-width: 380px;
  color: #374151;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: help;
}

.algo-tooltip {
  position: fixed;
  z-index: 9999;
  max-width: 460px;
  padding: 10px 12px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  box-shadow: 0 10px 22px rgba(0,0,0,0.12);
  color: #111827;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  pointer-events: none;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .field {
    width: 100%;
  }

  .field-actions {
    margin-left: 0;
    margin-top: 8px;
  }

  .algo-actions {
    justify-content: flex-start;
  }

  .pager {
    flex-wrap: wrap;
    justify-content: center;
  }
}
</style>