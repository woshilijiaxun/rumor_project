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
          <h1>识别计算</h1>
          <p class="subtitle">上传数据并使用算法进行识别计算</p>
        </div>
        <button class="history-btn" type="button" @click="openHistoryModal">识别历史</button>
      </div>
    </div>

    <div class="content-wrapper">
      <!-- 上方：选择数据源 / 选择算法 并排 -->
      <div class="top-row">
        <!-- 选择数据源 -->
        <div class="card">
          <h2>选择数据源</h2>
          
          <!-- 使用已有文件 -->
          <div class="form-group">
            <label>选择文件</label>
            <button 
              @click="openFileModal" 
              class="form-control file-select-btn"
              :disabled="loadingExistingFiles"
            >
              <span v-if="!selectedExistingFile" class="placeholder">点击选择文件</span>
              <span v-else class="selected-file">{{ getFileNameWithoutExt(selectedExistingFile.original_name) }}</span>
            </button>
            <p v-if="selectedExistingFile" class="file-hint">
              {{ getFileExtension(selectedExistingFile.original_name) }} · {{ formatFileSize(selectedExistingFile.size_bytes) }}
            </p>
          </div>

          <!-- 待确认选择区域 -->
          <div v-if="tempSelectedFile && tempSelectedFile?.id !== selectedExistingFile?.id" class="confirm-bar">
            <div class="confirm-info">
              <div class="name">{{ getFileNameWithoutExt(tempSelectedFile.original_name) }}</div>
              <div class="meta">
                <span class="file-type">{{ getFileExtension(tempSelectedFile.original_name) }}</span>
                <span class="file-size">{{ formatFileSize(tempSelectedFile.size_bytes) }}</span>
                <span class="file-date">{{ formatDate(tempSelectedFile.created_at) }}</span>
              </div>
            </div>
            <div class="confirm-actions">
              <button class="btn btn-primary" @click="confirmTempFile">确认选择文件</button>
              <button class="btn btn-secondary" @click="openFileModal">重新选择</button>
            </div>
          </div>

          <!-- 已确认文件的操作区域 -->
          <div v-if="selectedExistingFile && !(tempSelectedFile && tempSelectedFile?.id !== selectedExistingFile?.id)" class="file-actions">
            <button class="btn btn-primary" @click="visualizeNetwork(selectedExistingFile)">可视化网络</button>
          </div>
        </div>

        <!-- 选择算法 -->
        <div class="card">
          <h2>选择算法</h2>
          <div class="form-group algorithm-group">
            <label>可用算法</label>
            <div 
              class="algorithm-select-wrapper"
              @mouseenter="handleAlgoSelectMouseEnter"
              @mouseleave="handleAlgoSelectMouseLeave"
            >
              <select v-model="selectedAlgorithm" class="form-control" :disabled="algLoading">
                <option value="">-- 请选择算法 --</option>
                <option v-for="algo in availableAlgorithms" :key="algo.id" :value="algo.algo_key" :disabled="!algo.algo_key">
                  {{ (algo.type ? (algo.name + ' - ' + algo.type) : algo.name) + (!algo.algo_key ? '（请先配置 algo_key）' : '') }}
                </option>
              </select>
              <div v-if="showAlgoTooltip && currentAlgoDescription" class="algorithm-tooltip">
                {{ currentAlgoDescription }}
              </div>
            </div>
            <div class="form-hint" v-if="algLoading">算法列表加载中...</div>
            <div class="form-error" v-else-if="algError">
              {{ algError }}
              <button class="link-btn" type="button" @click="fetchAlgorithms">重试</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 下方：左侧网络拓扑（在数据源下方），右侧识别结果（在算法下方） -->
      <div class="middle-actions">
        <button 
          @click="startIdentification" 
          :disabled="!canStartIdentification"
          class="btn btn-primary"
        >
          开始识别
        </button>
        <button @click="resetForm" class="btn btn-secondary">
          重置
        </button>
      </div>

      <div class="bottom-row">
        <div class="left-panel">
          <!-- 网络可视化卡片 -->
          <div class="card" v-if="!(tempSelectedFile && tempSelectedFile?.id !== selectedExistingFile?.id)">
            <h2>网络拓扑可视化</h2>
            <div v-if="visualLoading" class="loading-state">
              <p>可视化生成中...</p>
            </div>
            <div v-else-if="visualError" class="error-state">
              <p>{{ visualError }}</p>
              <div class="action-buttons">
                <button class="btn btn-primary" :disabled="!selectedExistingFile" @click="visualizeNetwork(selectedExistingFile)">重试</button>
                <button class="btn btn-secondary" @click="clearVisualization">清空</button>
              </div>
            </div>
            <div v-else-if="visualData" class="visual-content">
              <div class="visual-meta">
                <div class="visual-meta-left">
                  <button
                    class="non-topk-toggle"
                    type="button"
                    :aria-pressed="nonTopKGray"
                    @click="toggleNonTopKGray"
                    :title="nonTopKGray ? '当前：非Top-K置灰（点击恢复蓝色）' : '当前：非Top-K蓝色（点击置灰）'"
                  >
                    <span class="toggle-dot" :class="{ on: nonTopKGray }"></span>
                    <span class="toggle-text">非Top-K{{ nonTopKGray ? '置灰' : '蓝色' }}</span>
                  </button>
                </div>

                <div class="visual-meta-right">
                  <span>文件：{{ getFileNameWithoutExt(selectedExistingFile?.original_name || visualData?.file?.original_name) }}</span>
                  <span>节点：{{ visualData?.graph?.meta?.nodes || 0 }}</span>
                  <span>边：{{ visualData?.graph?.meta?.edges || 0 }}</span>
                  <span v-if="visualData?.graph?.meta?.truncated" class="warning">已截断至 {{ visualData?.graph?.meta?.max_edges }} 条边</span>
                </div>
              </div>
              <GraphView v-if="visualData?.graph" :graph="visualData.graph" :highlight-map="topKHighlightMap" :non-topk-gray="nonTopKGray" height="480px" />
              <div class="action-buttons">
                <button class="btn btn-secondary" @click="clearVisualization">清空</button>
              </div>
            </div>
            <div v-else class="empty-state">
              <p>暂无网络拓扑</p>
              <p class="hint">选择文件后，点击"可视化网络"按钮</p>
            </div>
          </div>

        </div>

        <div class="right-panel">
          <div class="card">
            <h2>识别结果</h2>
            
            <!-- 进度条 -->
            <div v-if="isProcessing" class="progress-section">
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: progress + '%' }"></div>
              </div>
              <p class="progress-text">处理中... {{ progress }}%</p>
              <p class="status-text">{{ statusMessage }}</p>
            </div>

            <!-- 结果表格 -->
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

              <div class="table-wrapper">
                <table class="results-table">
                  <thead>
                    <tr>
                      <th>序号</th>
                      <th>节点</th>
                      <th>识别结果</th>
                      <th>重要程度</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(result, index) in displayedResults" :key="index">
                      <td>{{ index + 1 }}</td>
                      <td class="data-cell">{{ result.input }}</td>
                      <td class="result-cell">{{ formatResultValue(result.output) }}</td>
                      <td class="importance-cell">
                        <span class="importance-dot" :style="{ backgroundColor: getImportanceColor(result.output) }"></span>
                        <span class="importance-text">{{ getImportanceText(result.output) }}</span>
                      </td>

                    </tr>
                  </tbody>
                </table>
              </div>

              <div class="action-buttons">
                <button @click="exportResults" class="btn btn-primary">
                  导出结果
                </button>
                <button @click="clearResults" class="btn btn-secondary">
                  清空结果
                </button>
              </div>
            </div>

            <!-- 空状态 -->
            <div v-else class="empty-state">
              <p>暂无识别结果</p>
              <p class="hint">选择文件和算法后，点击"开始识别"按钮</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 文件选择弹出框（独立于布局） -->
      <div v-if="showFileModal" class="modal-overlay" @click.self="closeFileModal">
        <div class="modal-content">
          <div class="modal-header">
            <h3>选择文件</h3>
            <button class="modal-close" @click="closeFileModal">×</button>
          </div>
          <div class="modal-body">
            <div v-if="loadingExistingFiles" class="loading-state">
              <p>加载文件列表中...</p>
            </div>
            <div v-else-if="existingFilesError" class="error-state">
              <p>{{ existingFilesError }}</p>
              <button @click="loadExistingFiles" class="retry-btn">重试</button>
            </div>
            <template v-else>
              <div class="existing-filter-bar">
                <input 
                  v-model="existingSearch" 
                  type="text" 
                  class="existing-search-input" 
                  placeholder="搜索已有文件名或类型..."
                />
              </div>
              <div v-if="totalExistingFiles === 0" class="empty-state">
                <p>暂无可用文件</p>
              </div>
              <div v-else class="files-list" ref="filesListRef">
                <div 
                  v-for="file in displayedExistingFiles" 
                  :key="file.id"
                  class="file-item"
                  :class="{ selected: tempSelectedFile?.id === file.id }"
                  @click="selectTempFileAndClose(file)"
                >
                  <div class="file-info">
                    <div class="file-name">{{ getFileNameWithoutExt(file.original_name) }}</div>
                    <div class="file-meta">
                      <span class="file-type">{{ getFileExtension(file.original_name) }}</span>
                      <span class="file-size">{{ formatFileSize(file.size_bytes) }}</span>
                      <span class="file-date">{{ formatDate(file.created_at) }}</span>
                    </div>
                  </div>
                  <div class="file-checkbox">
                    <input 
                      type="radio" 
                      :checked="tempSelectedFile?.id === file.id"
                      @change="selectTempFileAndClose(file)"
                    />
                  </div>
                </div>
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>
    <TaskHistoryModal
      v-if="showHistoryModal"
      :tasks="historyTasks"
      :total-pages="historyTotalPages"
      :current-page="historyPage"
      :loading="historyLoading"
      :error="historyError"
      @close="closeHistoryModal"
      @refresh="onHistoryRefresh"
      @page-change="onHistoryPageChange"
      @view-details="onHistoryViewDetails"
      @delete="onHistoryDelete"
    />
  </div>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import GraphView from './components/GraphView.vue'
import ErrorModal from './components/ErrorModal.vue'
import TaskHistoryModal from './components/TaskHistoryModal.vue'
import { identificationService } from './services/identificationService'

export default {
  name: 'IdentificationPage',
  components: { GraphView, ErrorModal, TaskHistoryModal },
  setup() {
    const router = useRouter()
    const selectedExistingFile = ref(null)
    const existingFiles = ref([]) // 后端返回的所有文件（本页最多100条）
    const displayedExistingFiles = ref([]) // 当前显示的文件（分页后）
    const existingSearch = ref('')
    const filesPerPage = 2
    const currentFilesPage = ref(1)
    const filesListRef = ref(null)
    const loadingExistingFiles = ref(false)
    const loadingMoreExisting = ref(false)
    const existingFilesError = ref('')
    const showFileModal = ref(false)

    // 新增：待确认文件与可视化状态
    const tempSelectedFile = ref(null)
    const visualLoading = ref(false)
    const visualError = ref('')
    const visualData = ref(null)

    const filteredExistingFiles = computed(() => {
      const kw = (existingSearch.value || '').trim().toLowerCase()
      if (!kw) return existingFiles.value
      return existingFiles.value.filter(f => {
        const name = (f.original_name || '').toLowerCase()
        const type = (f.mime_type || '').toLowerCase()
        return name.includes(kw) || type.includes(kw)
      })
    })

    const totalExistingFiles = computed(() => filteredExistingFiles.value.length)

    const recalcDisplayed = () => {
      const end = currentFilesPage.value * filesPerPage
      displayedExistingFiles.value = filteredExistingFiles.value.slice(0, end)
    }
    
    const selectedAlgorithm = ref('')

    // 算法提示（hover 时展示，离开隐藏）
    const showAlgoTooltip = ref(false)
    const currentAlgoDescription = ref('')

    // 历史记录弹窗
    const showHistoryModal = ref(false)
    const historyLoading = ref(false)
    const historyError = ref('')
    const historyTasks = ref([])
    const historyPage = ref(1)
    const historyPageSize = 20
    const historyTotalPages = ref(1)

    // 错误弹窗
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

    // 异步识别任务状态
    const currentTaskId = ref('')
    const isProcessing = ref(false)
    const progress = ref(0)
    const statusMessage = ref('')
    const results = ref([])
    const resultsMap = ref(null) // 原始 map：{ node_id: node_value }

    // Top-K 展示
    const topK = ref(10)

    const pollTimer = ref(null)

    // 从算法列表接口加载可用算法，替换本地写死数据
    const algorithms = ref([])
    const algLoading = ref(false)
    const algError = ref('')
    const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:5001/api'
    const token = (typeof window !== 'undefined') ? localStorage.getItem('token') : ''

    const availableAlgorithms = computed(() => {
      return algorithms.value.filter(a => (a.status || 'active') === 'active')
    })

    const fetchAlgorithms = async () => {
      algLoading.value = true
      algError.value = ''
      try {
        const res = await fetch(`${apiBaseUrl}/algorithms?page=1&page_size=100`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        const data = await res.json()
        if (data.status === 'success') {
          algorithms.value = Array.isArray(data.data?.items) ? data.data.items : []
        } else {
          algError.value = data.message || '加载算法列表失败'
        }
      } catch (e) {
        algError.value = e.message || '加载算法列表失败'
      } finally {
        algLoading.value = false
      }
    }


    const canStartIdentification = computed(() => {
      return selectedExistingFile.value && selectedAlgorithm.value && !isProcessing.value
    })

    // 网络节点数量：优先用可视化 meta.nodes，其次用识别结果 map 的键数量
    const networkNodeCount = computed(() => {
      const fromGraph = visualData.value?.graph?.meta?.nodes
      if (Number.isFinite(Number(fromGraph))) return Number(fromGraph)
      const fromMap = resultsMap.value ? Object.keys(resultsMap.value).length : 0
      return fromMap
    })

    // 表格展示：按识别结果（数值）从大到小排序
    const formatResultValue = (v) => {
      const n = Number(v)
      if (!Number.isFinite(n)) return '-'
      return n.toFixed(4)
    }

    // 重要程度（与详情页同一套逻辑）
    const getImportanceLevel = (v) => {
      const n = Number(v)
      if (!Number.isFinite(n)) return 0
      const list = sortedResults.value
      if (!list || list.length === 0) return 0
      const maxV = Number(list[0]?.output)
      const minV = Number(list[list.length - 1]?.output)
      if (!Number.isFinite(maxV) || !Number.isFinite(minV)) return 0
      if (maxV === minV) return 3
      const ratio = (n - minV) / (maxV - minV)
      if (ratio >= 0.75) return 4
      if (ratio >= 0.5) return 3
      if (ratio >= 0.25) return 2
      return 1
    }

    const getImportanceColor = (v) => {
      const level = getImportanceLevel(v)
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

    // Top-K 的实际生效值：默认 10，但如果网络节点数 < 10 则显示全部
    const effectiveTopK = computed(() => {
      const total = sortedResults.value.length
      if (total <= 0) return 0
      const baseDefault = networkNodeCount.value > 0 ? Math.min(10, networkNodeCount.value) : Math.min(10, total)

      const k = Number(topK.value)
      const desired = Number.isFinite(k) && k > 0 ? k : baseDefault

      // 规则：网络节点数 < 10 时默认显示全部（等价于显示 total）
      if (networkNodeCount.value > 0 && networkNodeCount.value < 10) {
        return total
      }

      return Math.min(desired, total)
    })

    const displayedResults = computed(() => {
      return sortedResults.value.slice(0, effectiveTopK.value)
    })

    // 左侧图 Top-K 高亮映射：key=nodeId(String)，value=颜色（与右侧“重要程度”一致）
    // 严格按 nodeId 精确匹配：只有图中存在该节点 id 才会染色；否则忽略，避免乱染。
    const graphNodeIdSet = computed(() => {
      const nodes = visualData.value?.graph?.nodes || []
      const set = new Set()
      nodes.forEach(n => set.add(String(n.id)))
      return set
    })

    // 默认：首次可视化时非Top-K节点显示为蓝色
    const nonTopKGray = ref(false)

    const topKHighlightMap = computed(() => {
      const map = {}
      const set = graphNodeIdSet.value
      displayedResults.value.forEach((r) => {
        const nodeId = String(r.input)
        if (!set.has(nodeId)) return
        map[nodeId] = getImportanceColor(r.output)
      })
      return map
    })

    const toggleNonTopKGray = () => {
      nonTopKGray.value = !nonTopKGray.value
    }

    const hasMoreExistingFiles = computed(() => {
      return displayedExistingFiles.value.length < totalExistingFiles.value
    })

    const loadExistingFiles = async () => {
      loadingExistingFiles.value = true
      existingFilesError.value = ''
      currentFilesPage.value = 1
      try {
        const response = await axios.get('/api/uploads', { 
          params: { page: 1, page_size: 100 } 
        })
        if (response.data?.status === 'success') {
          const data = response.data.data || {}
          const items = Array.isArray(data.items) ? data.items : (Array.isArray(data) ? data : [])
          existingFiles.value = items
          currentFilesPage.value = 1
          displayedExistingFiles.value = filteredExistingFiles.value.slice(0, filesPerPage)
          await nextTick()
          const el = filesListRef.value
          if (el) el.scrollTop = 0
          attachInfiniteScroll()
        } else {
          existingFilesError.value = response.data?.message || '获取文件列表失败'
          displayedExistingFiles.value = []
          totalExistingFiles.value = 0
        }
      } catch (error) {
        existingFilesError.value = error.response?.data?.message || error.message || '获取文件列表失败'
        displayedExistingFiles.value = []
        totalExistingFiles.value = 0
      } finally {
        loadingExistingFiles.value = false
      }
    }

    const loadMoreExistingFiles = () => {
      if (!hasMoreExistingFiles.value) return
      const nextPage = currentFilesPage.value + 1
      const start = (nextPage - 1) * filesPerPage
      const end = start + filesPerPage
      displayedExistingFiles.value = filteredExistingFiles.value.slice(0, end)
      currentFilesPage.value = nextPage
    }

    // 无限滚动处理

    const onFilesListScroll = () => {
      const el = filesListRef.value
      if (!el || loadingExistingFiles.value) return
      const threshold = 16 // 距底部阈值（像素）
      const reachBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - threshold
      if (reachBottom && hasMoreExistingFiles.value && !loadingMoreExisting.value) {
        loadingMoreExisting.value = true
        // 展示下一批（前端分页）
        loadMoreExistingFiles()
        // 立即释放，因前端分页为同步操作
        loadingMoreExisting.value = false
      }
    }

    const isScrollable = (el) => {
      return el && el.scrollHeight > el.clientHeight + 1
    }

    const ensureListScrollable = async () => {
      await nextTick()
      const el = filesListRef.value
      if (!el) return
      let safety = 0
      while (hasMoreExistingFiles.value && !isScrollable(el) && safety < 50) {
        loadMoreExistingFiles()
        await nextTick()
        safety++
      }
    }

    const attachInfiniteScroll = async () => {
      await nextTick()
      const el = filesListRef.value
      if (!el) return
      el.removeEventListener('scroll', onFilesListScroll)
      el.addEventListener('scroll', onFilesListScroll, { passive: true })
      // 初次进入或内容较少时，自动填充到可滚动或无更多
      await ensureListScrollable()
    }

    // 历史任务列表加载
    const loadHistoryTasks = async () => {
      historyLoading.value = true
      historyError.value = ''
      try {
        const res = await identificationService.getTasks({
          page: historyPage.value,
          page_size: historyPageSize
        })
        // 兼容返回结构：data.items 或 data.data.items
        const payload = res?.data || res?.data?.data || res?.data
        const items = Array.isArray(payload?.items) ? payload.items : (Array.isArray(payload) ? payload : [])
        historyTasks.value = items

        const totalPages = Number(payload?.total_pages)
        if (Number.isFinite(totalPages) && totalPages > 0) {
          historyTotalPages.value = totalPages
        } else {
          // 若后端没给 total_pages，退化为 1
          historyTotalPages.value = 1
        }
      } catch (e) {
        historyError.value = (e?.message || '加载历史记录失败').trim()
        historyTasks.value = []
        historyTotalPages.value = 1
      } finally {
        historyLoading.value = false
      }
    }

    const openHistoryModal = async () => {
      showHistoryModal.value = true
      historyPage.value = 1
      await loadHistoryTasks()
    }

    const closeHistoryModal = () => {
      showHistoryModal.value = false
      historyError.value = ''
    }

    const onHistoryPageChange = async (page) => {
      const p = Number(page)
      if (!Number.isFinite(p) || p <= 0) return
      historyPage.value = p
      await loadHistoryTasks()
    }

    const onHistoryRefresh = async () => {
      await loadHistoryTasks()
    }

    const onHistoryViewDetails = (task) => {
      const taskId = task?.task_id || task?.id
      if (!taskId) return
      closeHistoryModal()
      router.push(`/identification/history/${encodeURIComponent(taskId)}`)
    }

    // 兼容子组件透传的 delete 事件：删除成功后刷新列表
    const onHistoryDelete = async () => {
      await loadHistoryTasks()
    }

    const detachInfiniteScroll = () => {
      const el = filesListRef.value
      if (!el) return
      el.removeEventListener('scroll', onFilesListScroll)
    }

    // 搜索变化时，重置分页并重算显示，保持滚动容器在顶部，并保证可滚动
    watch(selectedAlgorithm, (v) => {
      // 选中算法后，预先准备好 hover 展示内容
      currentAlgoDescription.value = v ? getAlgorithmFullDescription(v) : ''
    })

    watch(existingSearch, async () => {
      if (showFileModal.value) {
        currentFilesPage.value = 1
        recalcDisplayed()
        await nextTick()
        const el = filesListRef.value
        if (el) el.scrollTop = 0
        await ensureListScrollable()
      }
    })

    onMounted(async () => {
      // 加载算法列表
      fetchAlgorithms()
    })

    onBeforeUnmount(() => {
      detachInfiniteScroll()
      // 组件卸载时停止轮询，避免内存泄漏
      stopPolling()
    })

    // 选择临时文件并关闭弹窗
    const selectTempFileAndClose = (file) => {
      tempSelectedFile.value = file
      closeFileModal()
    }

    // 确认临时文件为已选文件
    const confirmTempFile = () => {
      if (tempSelectedFile.value) {
        selectedExistingFile.value = tempSelectedFile.value
      }
    }

    // 触发网络可视化：请求后端图数据并渲染
    const visualizeNetwork = async (file) => {
      if (!file) return
      visualLoading.value = true
      visualError.value = ''
      visualData.value = null
      try {
        const res = await axios.get(`${apiBaseUrl}/network/graph`, {
          params: { file_id: file.id },
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

    const clearVisualization = () => {
      visualData.value = null
      visualError.value = ''
    }

    const openFileModal = async () => {
      showFileModal.value = true
      if (existingFiles.value.length === 0) {
        await loadExistingFiles()
      }
      await nextTick()
      attachInfiniteScroll()
    }

    const closeFileModal = () => {
      showFileModal.value = false
      detachInfiniteScroll()
      existingSearch.value = ''
      currentFilesPage.value = 1
      recalcDisplayed()
    }


    const getFileNameWithoutExt = (filename) => {
      if (!filename) return '-'
      const lastDotIndex = filename.lastIndexOf('.')
      return lastDotIndex > 0 ? filename.substring(0, lastDotIndex) : filename
    }

    const getFileExtension = (filename) => {
      if (!filename) return '-'
      const lastDotIndex = filename.lastIndexOf('.')
      if (lastDotIndex > 0) {
        const ext = filename.substring(lastDotIndex + 1).toUpperCase()
        return ext || '-'
      }
      return '-'
    }

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
        return dateStr
      }
    }

    const getAlgorithmFullDescription = (algoKey) => {
      const algo = algorithms.value.find(a => a.algo_key == algoKey)
      const desc = String(algo?.description || '').trim()
      return desc || '暂无描述'
    }


    const stopPolling = () => {
      if (pollTimer.value) {
        clearInterval(pollTimer.value)
        pollTimer.value = null
      }
    }

    const pollTaskUntilDone = async (taskId) => {
      stopPolling()

      return new Promise((resolve, reject) => {
        const startedAt = Date.now()
        const timeoutMs = 10 * 60 * 1000 // 10 分钟超时

        pollTimer.value = setInterval(async () => {
          try {
            if (!taskId) return

            // 超时保护
            if (Date.now() - startedAt > timeoutMs) {
              stopPolling()
              reject(new Error('任务处理超时'))
              return
            }

            const taskRes = await identificationService.getTask(taskId)
            const task = taskRes?.data || {}

            const p = Number(task.progress)
            progress.value = Number.isFinite(p) ? Math.max(0, Math.min(100, Math.floor(p))) : progress.value
            statusMessage.value = task.message || task.stage || '处理中...'

            if (task.status === 'succeeded') {
              stopPolling()
              resolve(task)
            } else if (task.status === 'failed') {
              stopPolling()
              const errMsg = task.error?.message || task.message || '任务失败'
              reject(new Error(errMsg))
            } else if (task.status === 'cancelled') {
              stopPolling()
              reject(new Error('任务已取消'))
            }
          } catch (e) {
            stopPolling()
            reject(e)
          }
        }, 1000)
      })
    }

    const startIdentification = async () => {
      if (!selectedExistingFile.value || !selectedAlgorithm.value) {
        alert('请选择文件和算法')
        return
      }

      // 如果已有轮询，先停掉
      stopPolling()

      isProcessing.value = true
      progress.value = 0
      statusMessage.value = '任务创建中...'
      results.value = []
      resultsMap.value = null
      currentTaskId.value = ''

      try {
        // 1) 创建任务
        const createRes = await identificationService.createTask(
          selectedExistingFile.value.id,
          String(selectedAlgorithm.value),
          {}
        )

        const taskId = createRes?.data?.task_id
        if (!taskId) throw new Error('后端未返回 task_id')
        currentTaskId.value = taskId

        statusMessage.value = '任务已创建，等待执行...'

        // 2) 轮询任务直到完成
        await pollTaskUntilDone(taskId)

        // 3) 获取结果
        statusMessage.value = '获取结果中...'
        const resultRes = await identificationService.getResult(taskId)
        const map = resultRes?.data?.result || {}
        resultsMap.value = map

        // 将 map 转为表格数据
        const rows = Object.entries(map).map(([nodeId, nodeValue]) => ({
          input: String(nodeId),
          output: nodeValue
        }))
        results.value = rows

        statusMessage.value = '识别完成'
        progress.value = 100

      } catch (error) {
        console.error('识别失败:', error)
        const msg = (error?.message || String(error) || '').trim()
        statusMessage.value = '识别失败: ' + (msg || '未知错误')

        // 特殊提示：算法实现未注册
        if (msg.includes('算法实现未注册') || msg.includes('ALGO_IMPL_NOT_FOUND')) {
          openErrorModal('算法实现未注册', msg)
        } else {
          openErrorModal('识别失败', msg)
        }
      } finally {
        isProcessing.value = false
      }
    }

    const resetForm = () => {
      stopPolling()
      selectedExistingFile.value = null
      selectedAlgorithm.value = ''
      currentTaskId.value = ''
      results.value = []
      resultsMap.value = null
      topK.value = 10
      progress.value = 0
      statusMessage.value = ''
    }

    const exportResults = () => {
      if (results.value.length === 0) {
        alert('没有结果可导出')
        return
      }

      const csv = [
        ['序号', '节点ID', '识别结果'],
        ...displayedResults.value.map((r, i) => [
          i + 1,
          r.input,
          formatResultValue(r.output)
        ])
      ]
        .map(row => row.join(','))
        .join('\n')

      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      link.setAttribute('download', `识别结果_${new Date().getTime()}.csv`)
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }

    const clearResults = () => {
      results.value = []
      resultsMap.value = null
      topK.value = 10
      progress.value = 0
      statusMessage.value = ''
    }

    const handleAlgoSelectMouseEnter = () => {
      if (selectedAlgorithm.value) {
        showAlgoTooltip.value = true
      }
    }

    const handleAlgoSelectMouseLeave = () => {
      showAlgoTooltip.value = false
    }

    return {
      selectedExistingFile,
      existingFiles,
      displayedExistingFiles,
      totalExistingFiles,
      existingSearch,
      filesListRef,
      loadingExistingFiles,
      existingFilesError,
      showFileModal,
      selectedAlgorithm,
      isProcessing,
      progress,
      statusMessage,
      results,
      algorithms,
      availableAlgorithms,
      algLoading,
      algError,
      fetchAlgorithms,
      canStartIdentification,
      hasMoreExistingFiles,
      loadExistingFiles,
      loadMoreExistingFiles,
      tempSelectedFile,
      visualLoading,
      visualError,
      visualData,
      openFileModal,
      closeFileModal,
      selectTempFileAndClose,
      confirmTempFile,
      visualizeNetwork,
      clearVisualization,
      getFileNameWithoutExt,
      getFileExtension,
      formatFileSize,
      formatDate,
      showAlgoTooltip,
      currentAlgoDescription,
      handleAlgoSelectMouseEnter,
      handleAlgoSelectMouseLeave,
      startIdentification,
      resetForm,
      exportResults,
      clearResults,
      currentTaskId,
      networkNodeCount,
      sortedResults,
      displayedResults,
      topK,
      effectiveTopK,
      formatResultValue,
      getImportanceColor,
      getImportanceText,
      showErrorModal,
      errorModalMessage,
      errorModalDetail,
      closeErrorModal,
      // 历史记录
      openHistoryModal,
      closeHistoryModal,
      showHistoryModal,
      historyTasks,
      historyPage,
      historyTotalPages,
      historyLoading,
      historyError,
      onHistoryRefresh,
      onHistoryPageChange,
      onHistoryViewDetails,
      onHistoryDelete,
      topKHighlightMap,
      nonTopKGray,
      toggleNonTopKGray
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
  margin-bottom: 30px;
}

.header-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.history-btn {
  padding: 8px 14px;
  border: 1px solid #1677ff;
  background: #1677ff;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  color: #fff;
  flex: 0 0 auto;
  transition: background-color 0.3s, border-color 0.3s;
}

.history-btn:hover {
  border-color: #0d5ccc;
  background: #0d5ccc;
}

.page-header h1 {
  font-size: 28px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 8px 0;
}

.subtitle {
  color: #6b7280;
  margin: 0;
  font-size: 14px;
}

.content-wrapper {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.top-row,
.bottom-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
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

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 8px;
}

.form-control {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.3s;
}

.form-control:focus {
  outline: none;
  border-color: #1677ff;
  box-shadow: 0 0 0 2px rgba(22, 119, 255, 0.1);
}

.file-selector {
  position: relative;
}

#fileInput {
  display: none;
}

.file-label {
  display: block;
  padding: 12px;
  border: 2px dashed #d1d5db;
  border-radius: 6px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  background-color: #f9fafb;
}

.file-label:hover {
  border-color: #1677ff;
  background-color: #f0f7ff;
}

.file-hint {
  font-size: 12px;
  color: #9ca3af;
  margin: 8px 0 0 0;
}

.radio-group {
  display: flex;
  gap: 20px;
  margin-bottom: 16px;
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #374151;
  user-select: none;
}

.radio-label input[type="radio"] {
  cursor: pointer;
  width: 16px;
  height: 16px;
}

.radio-label:hover {
  color: #1677ff;
}

.existing-files-container {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  overflow: hidden;
  max-height: 400px;
  overflow-y: auto;
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

.retry-btn {
  margin-top: 12px;
  padding: 6px 16px;
  background-color: #1677ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: background-color 0.3s;
}

.retry-btn:hover {
  background-color: #0d5ccc;
}

.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #f3f4f6;
  cursor: pointer;
  transition: background-color 0.2s;
}

.file-item:hover {
  background-color: #f9fafb;
}

.file-item.selected {
  background-color: #f0f7ff;
  border-left: 3px solid #1677ff;
  padding-left: 13px;
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #9ca3af;
}

.file-type {
  background-color: #f3f4f6;
  padding: 2px 6px;
  border-radius: 3px;
  color: #6b7280;
  font-weight: 500;
}

.file-size {
  color: #6b7280;
}

.file-date {
  color: #9ca3af;
}

.file-checkbox {
  margin-left: 12px;
  flex-shrink: 0;
}

.file-checkbox input[type="radio"] {
  cursor: pointer;
  width: 16px;
  height: 16px;
}

.load-more-area {
  display: flex;
  justify-content: center;
  padding: 12px 16px;
  border-top: 1px solid #f3f4f6;
  background: #fff;
}

.load-more-btn {
  padding: 8px 16px;
  background-color: #e5e7eb;
  border: none;
  border-radius: 6px;
  color: #374151;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.load-more-btn:hover {
  background-color: #d1d5db;
}

.algorithm-info {
  padding: 12px;
  background-color: #f3f4f6;
  border-radius: 6px;
  font-size: 13px;
  color: #4b5563;
}

.algorithm-info p {
  margin: 8px 0;
}

.param-value {
  display: inline-block;
  margin-left: 8px;
  font-weight: 600;
  color: #1677ff;
}

input[type="range"] {
  width: 100%;
  cursor: pointer;
}

.action-buttons {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}

.middle-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
}

.middle-actions .btn {
  flex: 0 0 auto;
  min-width: 160px;
}

.btn {
  flex: 1;
  padding: 10px 16px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-primary {
  background-color: #1677ff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #0d5ccc;
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

.progress-section {
  padding: 20px;
  background-color: #f3f4f6;
  border-radius: 6px;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background-color: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 12px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #1677ff, #0d5ccc);
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 8px 0;
}

.status-text {
  font-size: 13px;
  color: #6b7280;
  margin: 0;
}

.results-section {
  padding: 0;
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

.results-summary.is-single {
  grid-template-columns: 1fr;
}

.summary-item .value.success {
  color: #10b981;
}

.summary-item .value.error {
  color: #ef4444;
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
  max-width: 150px;
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

.confidence-bar {
  display: inline-block;
  width: 60px;
  height: 6px;
  background-color: #e5e7eb;
  border-radius: 3px;
  overflow: hidden;
  margin-right: 8px;
  vertical-align: middle;
}

.confidence-fill {
  height: 100%;
  background: linear-gradient(90deg, #10b981, #059669);
}

.status-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.success {
  background-color: #d1fae5;
  color: #065f46;
}

.status-badge.failure {
  background-color: #fee2e2;
  color: #7f1d1d;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #9ca3af;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
}

.empty-state .hint {
  font-size: 12px;
  margin-top: 8px;
}

.file-select-btn {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding: 8px 12px !important;
  background-color: white;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  color: #374151;
  cursor: pointer;
  transition: all 0.3s;
  text-align: left;
}

.file-select-btn:hover:not(:disabled) {
  border-color: #1677ff;
  background-color: #f0f7ff;
}

.file-select-btn:disabled {
  background-color: #f3f4f6;
  cursor: not-allowed;
  color: #9ca3af;
}

.file-select-btn .placeholder {
  color: #9ca3af;
}

.file-select-btn .selected-file {
  color: #1f2937;
  font-weight: 500;
}

.confirm-bar {
  margin-top: 12px;
  padding: 12px;
  border: 1px dashed #d1d5db;
  border-radius: 6px;
  background-color: #f9fafb;
}
.confirm-info .name {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}
.confirm-info .meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #6b7280;
  margin-top: 6px;
}
.confirm-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
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

/* 更精致的开关样式（不占一整行，不会像大按钮一样突兀） */
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
  background: #1677ff; /* 蓝色状态 */
  box-shadow: inset 0 0 0 1px rgba(0,0,0,0.08);
}

.toggle-dot.on {
  background: #9ca3af; /* 置灰状态 */
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
.visual-placeholder {
  border: 1px dashed #d1d5db;
  border-radius: 6px;
  padding: 40px 16px;
  text-align: center;
  color: #9ca3af;
  background-color: #f9fafb;
}

.file-actions {
  display: flex;
  justify-content: center;
  margin-top: 12px;
}
.file-actions .btn {
  flex: 0 0 auto;
  min-width: 120px;
}

/* 弹出框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  color: #6b7280;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s;
}

.modal-close:hover {
  color: #1f2937;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
}

.existing-filter-bar {
  margin-bottom: 16px;
}

.existing-search-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.3s;
}

.existing-search-input:focus {
  outline: none;
  border-color: #1677ff;
  box-shadow: 0 0 0 2px rgba(22, 119, 255, 0.1);
}

.algorithm-select-wrapper {
  position: relative;
}

.algorithm-tooltip {
  position: absolute;
  left: 0;
  top: calc(100% + 8px);
  width: 100%;
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #e5e7eb;
  font-size: 12px;
  line-height: 1.5;
  padding: 10px 12px;
  border-radius: 8px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.18);
  z-index: 20;
  white-space: pre-wrap;
}

@media (max-width: 1200px) {
  .content-wrapper {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .identification-container {
    padding: 12px;
  }

  .page-header h1 {
    font-size: 22px;
  }
}
</style>

