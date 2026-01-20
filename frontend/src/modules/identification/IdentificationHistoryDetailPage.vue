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
        <div class="header-actions-right">
          <button class="back-btn refresh-btn" type="button" @click="reloadAll">刷新</button>
          <button class="back-btn" type="button" @click="goBack">返回</button>
        </div>
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
        </div>
      </div>

      <!-- middle-actions 已移除：进入页面会自动可视化，刷新按钮已移至右上角 -->

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
                <div class="visual-meta-left">
                  <button
                    class="non-topk-toggle"
                    type="button"
                    :aria-pressed="nonTopkGray"
                    @click="toggleNonTopKGray"
                    :title="nonTopkGray ? '当前：非Top-K置灰（点击恢复蓝色）' : '当前：非Top-K蓝色（点击置灰）'"
                  >
                    <span class="toggle-dot" :class="{ on: nonTopkGray }"></span>
                    <span class="toggle-text">非Top-K{{ nonTopkGray ? '置灰' : '蓝色' }}</span>
                  </button>
                </div>

                <div class="visual-meta-right">
                  <span>节点：{{ visualData?.graph?.meta?.nodes || 0 }}</span>
                  <span>边：{{ visualData?.graph?.meta?.edges || 0 }}</span>
                  <span v-if="visualData?.graph?.meta?.truncated" class="warning">已截断至 {{ visualData?.graph?.meta?.max_edges }} 条边</span>
                </div>
              </div>

              <GraphView3D
                v-if="visualData?.graph?.type === 'multilayer'"
                :graph="visualData.graph"
                :highlight-map="highlightMap"
                :non-topk-gray="nonTopkGray"
                height="480px"
              />
              <GraphView
                v-else-if="visualData?.graph"
                :graph="visualData.graph"
                :highlight-map="highlightMap"
                :non-topk-gray="nonTopkGray"
                height="480px"
              />
            </div>
            <div v-else class="empty-state">
              <p>暂无网络拓扑</p>
              <p class="hint">进入页面后会自动加载可视化</p>
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
              <div class="results-summary" :class="{ 'is-single': networkNodeCount > 0 && networkNodeCount < 10 }">
                <div class="summary-item">
                  <span class="label">网络总节点数:</span>
                  <span class="value">{{ networkNodeCount }}</span>
                </div>

                <div class="summary-item topk-item" v-if="!(networkNodeCount > 0 && networkNodeCount < 10)">
                  <span class="label">展示 Top-K:</span>
                  <select v-model.number="topK" class="topk-select">
                    <option :value="10">Top-10</option>
                    <option :value="20">Top-20</option>
                    <option :value="50">Top-50</option>
                    <option :value="100">Top-100</option>
                  </select>
                  <span class="topk-hint">当前展示 {{ effectiveTopK }} 条</span>


                </div>

                <div class="summary-item" v-else>
                  <span class="label">展示范围:</span>
                  <span class="value">全部</span>


                </div>
              </div>

              <div class="report-section">
                <div class="report-header">
                  <h3 class="sub-title">智能报告分析</h3>
                  <button class="btn btn-secondary report-entry-btn" type="button" @click="goToReportPage">查看报告</button>
                </div>
                <div class="report-entry-hint">点击“查看报告”跳转到智能报告页面</div>
              </div>

              <div class="table-wrapper">
                <table class="results-table">
                  <thead>
                    <tr>
                      <th>序号</th>
                      <th>节点</th>
                      <th>识别结果</th>
                      <th>重要程度</th>
                      <th>度(degree)</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(r, i) in displayedResults" :key="i">
                      <td>{{ i + 1 }}</td>
                      <td class="data-cell">{{ r.input }}</td>
                      <td class="result-cell">{{ formatResultValue(r.output) }}</td>
                      <td class="importance-cell">
                        <span class="importance-dot" :style="{ backgroundColor: getImportanceColor(r.output) }"></span>
                        <span class="importance-text">{{ getImportanceText(r.output) }}</span>
                      </td>
                      <td class="degree-cell">{{ getDegreeFromReport(r.input) }}</td>
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
import GraphView3D from './components/GraphView3D.vue'
import ErrorModal from './components/ErrorModal.vue'

import { identificationService } from './services/identificationService'

export default {
  name: 'IdentificationHistoryDetailPage',
  components: { GraphView, GraphView3D, ErrorModal },
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

    const reportLoading = ref(false)
    const reportError = ref('')
    const report = ref(null)

    const visualLoading = ref(false)
    const visualError = ref('')
    const visualData = ref(null)

    // Top-K and sorting
    const topK = ref(10)

    // 与主页面一致：默认非Top-K为蓝色；可切换置灰
    const nonTopkGray = ref(false)

    const networkNodeCount = computed(() => {
      const fromGraph = visualData.value?.graph?.meta?.nodes
      if (Number.isFinite(Number(fromGraph))) return Number(fromGraph)
      return results.value.length
    })

    const sortedResults = computed(() => {
      const arr = Array.isArray(results.value) ? results.value.slice() : []
      arr.sort((a, b) => {
        const av = Number(a?.output)
        const bv = Number(b?.output)
        const aNum = Number.isFinite(av) ? av : -Infinity
        const bNum = Number.isFinite(bv) ? bv : -Infinity
        return bNum - aNum
      })
      return arr
    })

    const effectiveTopK = computed(() => {
      const total = sortedResults.value.length
      if (total <= 0) return 0
      const baseDefault = networkNodeCount.value > 0 ? Math.min(10, networkNodeCount.value) : Math.min(10, total)

      const k = Number(topK.value)
      const desired = Number.isFinite(k) && k > 0 ? k : baseDefault

      if (networkNodeCount.value > 0 && networkNodeCount.value < 10) {
        return total
      }

      return Math.min(desired, total)
    })

    const displayedResults = computed(() => {
      return sortedResults.value.slice(0, effectiveTopK.value)
    })

    // 给 GraphView 的节点上色映射：{ [nodeId]: color }
    // 这里沿用你在 GraphView 里现有的机制：有颜色 -> class=topk
    // 颜色规则：按 output 在 Top-K 内做归一化，从红->橙/黄 的渐变
    // 左侧图 Top-K 高亮映射：与主页面一致，使用“重要程度”颜色
    const graphNodeIdSet = computed(() => {
      const g = visualData.value?.graph
      const set = new Set()

      // 多层图：GraphView3D 以 rawId 作为高亮匹配 key
      if (g?.type === 'multilayer' && Array.isArray(g?.layers)) {
        g.layers.forEach(layer => {
          const ns = Array.isArray(layer?.nodes) ? layer.nodes : []
          ns.forEach(n => {
            const id = n?.id
            if (id == null) return
            set.add(String(id))
          })
        })
        return set
      }

      // 单层图
      const nodes = g?.nodes || []
      nodes.forEach(n => set.add(String(n.id)))
      return set
    })

    const highlightMap = computed(() => {
      const map = {}
      const set = graphNodeIdSet.value
      displayedResults.value.forEach((r) => {
        const nodeId = String(r.input)
        if (!set.has(nodeId)) return
        map[nodeId] = getImportanceColor(r.output)
      })
      return map
    })

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

    // 重要程度：用颜色表示（按当前 Top-K 结果做相对归一化）
    const getImportanceLevel = (v) => {
      const n = Number(v)
      if (!Number.isFinite(n)) return 0

      const list = sortedResults.value
      if (!list || list.length === 0) return 0

      const maxV = Number(list[0]?.output)
      const minV = Number(list[list.length - 1]?.output)
      if (!Number.isFinite(maxV) || !Number.isFinite(minV)) return 0
      if (maxV === minV) return 3

      const ratio = (n - minV) / (maxV - minV) // 0..1
      if (ratio >= 0.75) return 4
      if (ratio >= 0.5) return 3
      if (ratio >= 0.25) return 2
      return 1
    }

    const getImportanceColor = (v) => {
      const level = getImportanceLevel(v)
      // 4: 高(红) 3: 较高(橙) 2: 中(黄) 1: 低(绿) 0: 无(灰)
      if (level === 4) return '#ef4444'
      if (level === 3) return '#f59e0b'
      if (level === 2) return '#eab308'
      if (level === 1) return '#10b981'
      return '#9ca3af'
    }

    const getImportanceText = (v) => {
      const level = getImportanceLevel(v)
      if (level === 4) return '高'
      if (level === 3) return '较高'
      if (level === 2) return '中'
      if (level === 1) return '低'
      return '-'
    }

    const getDegreeFromReport = (nodeId) => {
      if (!report.value?.top_nodes) return '-'
      const node = report.value.top_nodes.find(n => n.node_id === String(nodeId))
      return node?.degree ?? '-'
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

    const loadReport = async ({ top_n = 20, max_edges = 200000 } = {}) => {
      if (!taskId) return
      reportLoading.value = true
      reportError.value = ''
      report.value = null
      try {
        const res = await identificationService.getReport(taskId, { top_n, max_edges })
        report.value = res?.data?.report || null
      } catch (e) {
        reportError.value = e?.message || '加载报告失败'
      } finally {
        reportLoading.value = false
      }
    }

    const _graphCacheKey = (fid, maxEdges) => {
      return `graph_cache:v1:file:${fid}:max_edges:${maxEdges}`
    }

    const _getCachedGraph = (fid, maxEdges) => {
      try {
        const raw = sessionStorage.getItem(_graphCacheKey(fid, maxEdges))
        if (!raw) return null
        const parsed = JSON.parse(raw)
        // 简单校验结构
        if (parsed && typeof parsed === 'object' && parsed.graph) return parsed
      } catch {
        // ignore
      }
      return null
    }

    const _setCachedGraph = (fid, maxEdges, data) => {
      try {
        sessionStorage.setItem(_graphCacheKey(fid, maxEdges), JSON.stringify(data))
      } catch {
        // ignore quota / security error
      }
    }

    const visualize = async ({ force = false } = {}) => {
      const fid = fileId.value
      if (!fid) return

      const maxEdges = 10000

      // 1) 前端 session 缓存命中：直接秒开
      if (!force) {
        const cached = _getCachedGraph(fid, maxEdges)
        if (cached) {
          visualError.value = ''
          visualLoading.value = false
          visualData.value = cached
          return
        }
      }

      // 2) 未命中：请求后端（后端也可能命中 DB 缓存）
      visualLoading.value = true
      visualError.value = ''
      visualData.value = null
      try {
        const res = await axios.get(`${apiBaseUrl}/network/graph`, {
          params: { file_id: fid, max_edges: maxEdges, force: force ? 1 : 0 },
          headers: { 'Authorization': `Bearer ${token}` }
        })
        if (res.data?.status === 'success') {
          visualData.value = res.data.data
          // 写入 session 缓存（只缓存 data 部分）
          _setCachedGraph(fid, maxEdges, res.data.data)
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
      await loadReport({ top_n: 20, max_edges: 200000 })
      // 进入详情页后自动触发可视化（不再需要手动点按钮）
      await visualize({ force: true })
    }

    const goBack = () => {
      router.push('/identification')
    }

    const goToReportPage = () => {
      if (!taskId) {
        openErrorModal('缺少任务 ID', '无法跳转到报告页面')
        return
      }
      router.push(`/identification/report/${encodeURIComponent(taskId)}`)
    }

    onMounted(async () => {
      // 首次进入：优先使用 session 缓存加速（不强制刷新）
      await loadTask()
      await loadResult()
      await loadReport({ top_n: 20, max_edges: 200000 })
      await visualize({ force: false })
    })

    const toggleNonTopKGray = () => {
      nonTopkGray.value = !nonTopkGray.value
    }

    return {
      taskId,
      task,
      taskLoading,
      resultLoading,
      resultError,
      results,
      reportLoading,
      reportError,
      report,
      topK,
      highlightMap,
      nonTopkGray,
      toggleNonTopKGray,
      networkNodeCount,
      sortedResults,
      displayedResults,
      effectiveTopK,
      visualLoading,
      visualError,
      visualData,
      fileId,
      visualize,
      reloadAll,
      goBack,
      goToReportPage,
      formatFileSize,
      formatDate,
      prettyJson,
      formatResultValue,
      getImportanceColor,
      getImportanceText,
      getDegreeFromReport,
      showErrorModal,
      errorModalMessage,
      errorModalDetail,
      closeErrorModal
    }
  }
}
</script>

<style scoped>
.report-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.report-entry-btn {
  flex: 0 0 auto;
  padding: 8px 12px;
}

.report-entry-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #6b7280;
}

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

.header-actions-right {
  display: flex;
  align-items: center;
  gap: 10px;
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

.visual-content {
  padding: 8px 0;
}

.visual-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.visual-meta-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.visual-meta-right {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.non-topk-toggle {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid #e5e7eb;
  background: #fff;
  color: #374151;
  font-size: 12px;
  line-height: 1;
  cursor: pointer;
  user-select: none;
  transition: background-color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

.non-topk-toggle:hover {
  border-color: #cbd5e1;
  background: #f9fafb;
}

.non-topk-toggle:active {
  transform: translateY(1px);
}

.non-topk-toggle:focus {
  outline: none;
  box-shadow: 0 0 0 3px rgba(22, 119, 255, 0.18);
  border-color: #93c5fd;
}

.toggle-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #1677ff;
  box-shadow: inset 0 0 0 1px rgba(0,0,0,0.08);
}

.toggle-dot.on {
  background: #9ca3af;
}

.toggle-text {
  font-weight: 600;
}

@media (max-width: 520px) {
  .visual-meta {
    align-items: flex-start;
  }
  .visual-meta-right {
    justify-content: flex-start;
  }
}

.warning {
  color: #f59e0b;
}

.results-summary {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 20px;
  padding: 16px;
  background-color: #f9fafb;
  border-radius: 6px;
}

.results-summary.is-single {
  grid-template-columns: 1fr;
}

.summary-item {
  text-align: center;
}

.summary-item .label {
  display: block;
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}

.summary-item .value {
  display: block;
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
}

.topk-item {
  text-align: left;
}

.topk-select {
  margin-top: 6px;
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}

.topk-hint {
  display: block;
  margin-top: 6px;
  font-size: 12px;
  color: #6b7280;
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

.importance-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.importance-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  display: inline-block;
}

.importance-text {
  font-size: 12px;
  color: #4b5563;
}

@media (max-width: 1200px) {
  .top-row,
  .bottom-row {
    grid-template-columns: 1fr;
  }
}
</style>
