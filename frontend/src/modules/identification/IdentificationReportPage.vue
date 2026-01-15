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
          <h1>智能报告</h1>
          <p class="subtitle">任务：{{ taskId }}</p>
        </div>
        <div class="header-actions-right">
          <button class="back-btn refresh-btn" type="button" @click="reload">刷新</button>
          <button class="back-btn" type="button" @click="exportReport" :disabled="reportExporting">{{ reportExporting ? '导出中...' : '导出报告' }}</button>
          <button class="back-btn" type="button" @click="goBack">返回</button>
        </div>
      </div>
    </div>

    <div class="content-wrapper">
      <div class="card">
        <div class="report-section">
          <h2>智能报告分析</h2>
          <ReportAnalysis
            :report="report"
            :loading="reportLoading"
            :error="reportError"
            :highlight-map="highlightMap"
            :non-topk-gray="nonTopkGray"
            @toggle-non-topk-gray="toggleNonTopkGray"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ErrorModal from './components/ErrorModal.vue'
import ReportAnalysis from './components/ReportAnalysis.vue'
import { identificationService } from './services/identificationService'

export default {
  name: 'IdentificationReportPage',
  components: { ErrorModal, ReportAnalysis },
  setup() {
    const route = useRoute()
    const router = useRouter()

    const taskId = String(route.params.taskId || '').trim()

    const reportLoading = ref(false)
    const reportError = ref('')
    const report = ref(null)

    // 报告页默认：非Top-K置灰（与识别计算页一致）
    const nonTopkGray = ref(true)

    const toggleNonTopkGray = () => {
      nonTopkGray.value = !nonTopkGray.value
    }

    const topNodesForHighlight = computed(() => {
      const secs = Array.isArray(report.value?.sections) ? report.value.sections : []
      const sec = secs.find(s => s?.id === 'key_nodes_and_propagation')
      const nodes = Array.isArray(sec?.data?.top_nodes) ? sec.data.top_nodes : []
      return nodes
    })

    // 重要程度颜色（与识别计算页一致）
    const getImportanceLevel = (v) => {
      const n = Number(v)
      if (!Number.isFinite(n)) return 0
      const list = topNodesForHighlight.value
      if (!list || list.length === 0) return 0

      const scores = list.map(x => Number(x?.score)).filter(x => Number.isFinite(x))
      if (scores.length === 0) return 0

      const maxV = Math.max(...scores)
      const minV = Math.min(...scores)
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

    const highlightMap = computed(() => {
      const map = {}
      const list = topNodesForHighlight.value
      list.forEach((r) => {
        const nodeId = String(r?.node_id)
        if (!nodeId) return
        map[nodeId] = getImportanceColor(r?.score)
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
        openErrorModal('加载报告失败', e?.message || String(e))
      } finally {
        reportLoading.value = false
      }
    }

    const reload = async () => {
      await loadReport({ top_n: 20, max_edges: 200000 })
    }

    const reportExporting = ref(false)

    const exportReport = async () => {
      if (reportExporting.value) return
      try {
        reportExporting.value = true

        const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:5001/api'
        const url = `${apiBaseUrl}/identification/tasks/${encodeURIComponent(taskId)}/report/html`

        const token = (typeof window !== 'undefined') ? localStorage.getItem('token') : ''
        const res = await fetch(url, {
          method: 'GET',
          headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        })

        if (!res.ok) {
          const text = await res.text().catch(() => '')
          throw new Error(text || `导出失败（HTTP ${res.status}）`)
        }

        const blob = await res.blob()
        const blobUrl = window.URL.createObjectURL(blob)

        const a = document.createElement('a')
        a.href = blobUrl
        a.download = `identification_report_${taskId}.html`
        document.body.appendChild(a)
        a.click()
        a.remove()

        window.URL.revokeObjectURL(blobUrl)
      } catch (e) {
        openErrorModal('导出报告失败', e?.message || String(e))
      } finally {
        reportExporting.value = false
      }
    }

    const goBack = () => {
      router.back()
    }

    onMounted(async () => {
      if (!taskId) {
        openErrorModal('缺少 taskId', '请从识别结果或识别历史详情页进入智能报告页面')
        return
      }
      await loadReport({ top_n: 20, max_edges: 200000 })
    })

    return {
      taskId,
      reportLoading,
      reportError,
      report,
      nonTopkGray,
      highlightMap,
      toggleNonTopkGray,
      reload,
      exportReport,
      reportExporting,
      goBack,
      showErrorModal,
      errorModalMessage,
      errorModalDetail,
      closeErrorModal,
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

.report-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>

