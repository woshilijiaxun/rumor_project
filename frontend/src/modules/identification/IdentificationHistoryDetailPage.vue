<template>
  <div class="identification-container">
    <ErrorModal
      :visible="showErrorModal"
      :message="errorModalMessage"
      :detail="errorModalDetail"
      @close="closeErrorModal"
    />

    <div class="page-header">
      <div class="header-row">
        <div>
          <h1>识别历史详情</h1>
          <p class="subtitle">任务：{{ taskId }}</p>
        </div>
        <button class="back-btn" type="button" @click="goBack">返回</button>
      </div>
    </div>

    <div class="content-wrapper">
      <!-- 上方：数据源 / 算法 并排（只读） -->
      <div class="top-row">
        <div class="card">
          <h2>数据源信息</h2>
          <div class="kv">
            <div class="k">文件ID</div>
            <div class="v">{{ task?.file_id ?? '-' }}</div>
          </div>
          <div class="kv" v-if="task?.file">
            <div class="k">文件名</div>
            <div class="v">{{ task?.file?.original_name || '-' }}</div>
          </div>
          <div class="kv" v-if="task?.file">
            <div class="k">大小</div>
            <div class="v">{{ formatFileSize(task?.file?.size_bytes) }}</div>
          </div>
          <div class="kv">
            <div class="k">创建时间</div>
            <div class="v">{{ formatDate(task?.created_at) }}</div>
          </div>
        </div>

        <div class="card">
          <h2>算法信息</h2>
          <div class="kv">
            <div class="k">algo_key</div>
            <div class="v">{{ task?.algorithm_key || task?.algo_key || '-' }}</div>
          </div>
          <div class="kv">
            <div class="k">状态</div>
            <div class="v">{{ task?.status || '-' }}</div>
          </div>
          <div class="kv" v-if="task?.params">
            <div class="k">参数</div>
            <div class="v"><pre class="pre">{{ prettyJson(task?.params) }}</pre></div>
          </div>
        </div>
      </div>

      <div class="middle-actions">
        <button class="btn btn-primary" type="button" :disabled="!fileId" @click="visualize">
          可视化网络
        </button>
        <button class="btn btn-secondary" type="button" @click="reloadAll">刷新</button>
      </div>

      <div class="bottom-row">
        <!-- 左：拓扑 -->
        <div class="left-panel">
          <div class="card">
            <h2>网络拓扑可视化</h2>

            <div v-if="visualLoading" class="loading-state">
              <p>可视化生成中...</p>
            </div>
            <div v-else-if="visualError" class="error-state">
              <p>{{ visualError }}</p>
            </div>
            <div v-else-if="visualData" class="visual-content">
              <div class="visual-meta">
                <span>节点：{{ visualData?.graph?.meta?.nodes || 0 }}</span>
                <span>边：{{ visualData?.graph?.meta?.edges || 0 }}</span>
                <span v-if="visualData?.graph?.meta?.truncated" class="warning">已截断至 {{ visualData?.graph?.meta?.max_edges }} 条边</span>
              </div>
              <GraphView v-if="visualData?.graph" :graph="visualData.graph" height="480px" />
            </div>
            <div v-else class="empty-state">
              <p>暂无网络拓扑</p>
              <p class="hint">点击上方“可视化网络”查看</p>
            </div>
          </div>
        </div>

        <!-- 右：结果 -->
        <div class="right-panel">
          <div class="card">
            <h2>识别结果</h2>

            <div v-if="taskLoading" class="loading-state">
              <p>任务信息加载中...</p>
            </div>

            <div v-else-if="resultLoading" class="loading-state">
              <p>结果加载中...</p>
            </div>

            <div v-else-if="resultError" class="error-state">
              <p>{{ resultError }}</p>
            </div>

            <div v-else-if="results.length > 0" class="results-section">
              <div class="table-wrapper">
                <table class="results-table">
                  <thead>
                    <tr>
                      <th>序号</th>
                      <th>节点</th>
                      <th>识别结果</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(r, i) in results" :key="i">
                      <td>{{ i + 1 }}</td>
                      <td class="data-cell">{{ r.input }}</td>
                      <td class="result-cell">{{ formatResultValue(r.output) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div v-else class="empty-state">
              <p>暂无识别结果</p>
              <p class="hint">可能任务未完成或后端未保存结果</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import GraphView from './components/GraphView.vue'
import ErrorModal from './components/ErrorModal.vue'
import { identificationService } from './services/identificationService'

export default {
  name: 'IdentificationHistoryDetailPage',
  components: { GraphView, ErrorModal },
  setup() {
    const route = useRoute()
    const router = useRouter()

    const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:5001/api'
    const token = (typeof window !== 'undefined') ? localStorage.getItem('token') : ''

    const taskId = String(route.params.taskId || '')

    const taskLoading = ref(false)
    const task = ref(null)

    const resultLoading = ref(false)
    const resultError = ref('')
    const results = ref([])

    const visualLoading = ref(false)
    const visualError = ref('')
    const visualData = ref(null)

    const showErrorModal = ref(false)
    const errorModalMessage = ref('')
    const errorModalDetail = ref('')

    const openErrorModal = (message, detail = '') => {
      showErrorModal.value = true
      errorModalMessage.value = message || '操作失败'
      errorModalDetail.value = detail || ''
    }
    const closeErrorModal = () => {
      showErrorModal.value = false
      errorModalMessage.value = ''
      errorModalDetail.value = ''
    }

    const fileId = computed(() => task.value?.file_id || task.value?.file?.id)

    const formatFileSize = (bytes) => {
      if (bytes == null) return '-'
      const units = ['B', 'KB', 'MB', 'GB', 'TB']
      let size = Number(bytes)
      let unitIndex = 0
      while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024
        unitIndex++
      }
      return `${size.toFixed(unitIndex > 0 ? 1 : 0)} ${units[unitIndex]}`
    }

    const formatDate = (dateStr) => {
      if (!dateStr) return '-'
      try {
        const date = new Date(dateStr)
        return date.toLocaleString('zh-CN')
      } catch {
        return String(dateStr)
      }
    }

    const prettyJson = (obj) => {
      try { return JSON.stringify(obj, null, 2) } catch { return String(obj) }
    }

    const formatResultValue = (v) => {
      const n = Number(v)
      if (!Number.isFinite(n)) return '-'
      return n.toFixed(4)
    }

    const loadTask = async () => {
      if (!taskId) return
      taskLoading.value = true
      try {
        const res = await identificationService.getTask(taskId)
        task.value = res?.data || null
      } catch (e) {
        openErrorModal('加载任务失败', e?.message || String(e))
      } finally {
        taskLoading.value = false
      }
    }

    const loadResult = async () => {
      if (!taskId) return
      resultLoading.value = true
      resultError.value = ''
      results.value = []
      try {
        const res = await identificationService.getResult(taskId)
        const map = res?.data?.result || {}
        const rows = Object.entries(map).map(([nodeId, nodeValue]) => ({
          input: String(nodeId),
          output: nodeValue
        }))
        results.value = rows
      } catch (e) {
        resultError.value = e?.message || '加载结果失败'
      } finally {
        resultLoading.value = false
      }
    }

    const visualize = async () => {
      const fid = fileId.value
      if (!fid) return
      visualLoading.value = true
      visualError.value = ''
      visualData.value = null
      try {
        const res = await axios.get(`${apiBaseUrl}/network/graph`, {
          params: { file_id: fid },
          headers: { 'Authorization': `Bearer ${token}` }
        })
        if (res.data?.status === 'success') {
          visualData.value = res.data.data
        } else {
          throw new Error(res.data?.message || '可视化加载失败')
        }
      } catch (e) {
        visualError.value = e.response?.data?.message || e.message || '可视化加载失败'
      } finally {
        visualLoading.value = false
      }
    }

    const reloadAll = async () => {
      await loadTask()
      await loadResult()
    }

    const goBack = () => {
      router.push('/identification')
    }

    onMounted(async () => {
      await reloadAll()
    })

    return {
      taskId,
      task,
      taskLoading,
      resultLoading,
      resultError,
      results,
      visualLoading,
      visualError,
      visualData,
      fileId,
      visualize,
      reloadAll,
      goBack,
      formatFileSize,
      formatDate,
      prettyJson,
      formatResultValue,
      showErrorModal,
      errorModalMessage,
      errorModalDetail,
      closeErrorModal
    }
  }
}
</script>

<style scoped>
.identification-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 20px;
}

.header-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.page-header h1 {
  font-size: 22px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 6px 0;
}

.subtitle {
  color: #6b7280;
  margin: 0;
  font-size: 13px;
}

.back-btn {
  padding: 8px 14px;
  border: 1px solid #d1d5db;
  background: #fff;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  color: #374151;
}

.back-btn:hover {
  border-color: #1677ff;
  color: #1677ff;
  background: #f0f7ff;
}

.content-wrapper {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.top-row,
.bottom-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  align-items: start;
}

.card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.card h2 {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 16px 0;
  padding-bottom: 12px;
  border-bottom: 1px solid #e5e7eb;
}

.kv {
  display: grid;
  grid-template-columns: 80px 1fr;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px dashed #eef2f7;
}

.kv:last-child {
  border-bottom: none;
}

.k {
  font-size: 12px;
  color: #6b7280;
}

.v {
  font-size: 13px;
  color: #374151;
  overflow-wrap: anywhere;
}

.pre {
  margin: 0;
  white-space: pre-wrap;
  font-size: 12px;
  color: #374151;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  padding: 10px;
  border-radius: 8px;
}

.middle-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
}

.btn {
  padding: 10px 16px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
}

.btn-primary {
  background-color: #1677ff;
  color: white;
}

.btn-primary:disabled {
  background-color: #bfdbfe;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: #e5e7eb;
  color: #374151;
}

.btn-secondary:hover {
  background-color: #d1d5db;
}

.loading-state,
.error-state,
.empty-state {
  padding: 20px;
  text-align: center;
  color: #6b7280;
}

.error-state {
  color: #ef4444;
}

.hint {
  font-size: 12px;
  margin-top: 6px;
  color: #9ca3af;
}

.visual-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.warning {
  color: #f59e0b;
}

.table-wrapper {
  overflow-x: auto;
  margin-bottom: 16px;
}

.results-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.results-table thead {
  background-color: #f3f4f6;
}

.results-table th {
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #374151;
  border-bottom: 1px solid #e5e7eb;
}

.results-table td {
  padding: 12px;
  border-bottom: 1px solid #e5e7eb;
  color: #4b5563;
}

.data-cell {
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-cell {
  font-weight: 500;
  color: #1f2937;
}

@media (max-width: 1200px) {
  .top-row,
  .bottom-row {
    grid-template-columns: 1fr;
  }
}
</style>

