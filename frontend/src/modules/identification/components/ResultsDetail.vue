<template>
  <div class="results-detail">
    <div class="detail-header">
      <h3>详细结果分析</h3>
      <button @click="closeDetail" class="close-btn">×</button>
    </div>

    <div class="detail-content">
      <!-- 统计信息 -->
      <div class="statistics-section">
        <h4>统计信息</h4>
        <div class="stats-grid">
          <div class="stat-card">
            <span class="stat-label">总条数</span>
            <span class="stat-value">{{ totalCount }}</span>
          </div>
          <div class="stat-card">
            <span class="stat-label">成功率</span>
            <span class="stat-value success">{{ successRate }}%</span>
          </div>
          <div class="stat-card">
            <span class="stat-label">平均置信度</span>
            <span class="stat-value">{{ avgConfidence }}</span>
          </div>
          <div class="stat-card">
            <span class="stat-label">处理耗时</span>
            <span class="stat-value">{{ processingTime }}s</span>
          </div>
        </div>
      </div>

      <!-- 分布图表 -->
      <div class="chart-section">
        <h4>置信度分布</h4>
        <div class="confidence-distribution">
          <div v-for="(count, range) in confidenceRanges" :key="range" class="range-bar">
            <span class="range-label">{{ range }}</span>
            <div class="bar-container">
              <div class="bar" :style="{ width: (count / maxRangeCount * 100) + '%' }"></div>
            </div>
            <span class="range-count">{{ count }}</span>
          </div>
        </div>
      </div>

      <!-- 错误分析 -->
      <div v-if="failureResults.length > 0" class="error-section">
        <h4>失败结果分析</h4>
        <div class="error-list">
          <div v-for="(result, index) in failureResults" :key="index" class="error-item">
            <span class="error-index">{{ index + 1 }}</span>
            <span class="error-input">{{ result.input }}</span>
            <span class="error-reason">{{ result.errorReason || '未知原因' }}</span>
          </div>
        </div>
      </div>

      <!-- 结果分类 -->
      <div class="classification-section">
        <h4>结果分类统计</h4>
        <div class="classification-list">
          <div v-for="(count, category) in categoryCounts" :key="category" class="classification-item">
            <span class="category-name">{{ category }}</span>
            <div class="category-bar">
              <div class="category-fill" :style="{ width: (count / maxCategoryCount * 100) + '%' }"></div>
            </div>
            <span class="category-count">{{ count }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'ResultsDetail',
  props: {
    results: {
      type: Array,
      required: true
    },
    processingTime: {
      type: Number,
      default: 0
    }
  },
  emits: ['close'],
  setup(props, { emit }) {
    const totalCount = computed(() => props.results.length)

    const successCount = computed(() => {
      return props.results.filter(r => r.status === 'success').length
    })

    const successRate = computed(() => {
      if (totalCount.value === 0) return 0
      return ((successCount.value / totalCount.value) * 100).toFixed(1)
    })

    const avgConfidence = computed(() => {
      if (totalCount.value === 0) return 0
      const sum = props.results.reduce((acc, r) => acc + (r.confidence || 0), 0)
      return (sum / totalCount.value).toFixed(3)
    })

    const failureResults = computed(() => {
      return props.results.filter(r => r.status === 'failure')
    })

    const confidenceRanges = computed(() => {
      const ranges = {
        '0-20%': 0,
        '20-40%': 0,
        '40-60%': 0,
        '60-80%': 0,
        '80-100%': 0
      }

      props.results.forEach(result => {
        const conf = (result.confidence || 0) * 100
        if (conf < 20) ranges['0-20%']++
        else if (conf < 40) ranges['20-40%']++
        else if (conf < 60) ranges['40-60%']++
        else if (conf < 80) ranges['60-80%']++
        else ranges['80-100%']++
      })

      return ranges
    })

    const maxRangeCount = computed(() => {
      return Math.max(...Object.values(confidenceRanges.value), 1)
    })

    const categoryCounts = computed(() => {
      const counts = {}
      props.results.forEach(result => {
        const output = result.output || '未分类'
        counts[output] = (counts[output] || 0) + 1
      })
      return counts
    })

    const maxCategoryCount = computed(() => {
      return Math.max(...Object.values(categoryCounts.value), 1)
    })

    const closeDetail = () => {
      emit('close')
    }

    return {
      totalCount,
      successRate,
      avgConfidence,
      failureResults,
      confidenceRanges,
      maxRangeCount,
      categoryCounts,
      maxCategoryCount,
      closeDetail
    }
  }
}
</script>

<style scoped>
.results-detail {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  overflow: hidden;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
  background-color: #f9fafb;
}

.detail-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  color: #9ca3af;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.3s;
}

.close-btn:hover {
  color: #1f2937;
}

.detail-content {
  padding: 20px;
}

.statistics-section,
.chart-section,
.error-section,
.classification-section {
  margin-bottom: 24px;
}

.statistics-section h4,
.chart-section h4,
.error-section h4,
.classification-section h4 {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 12px 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.stat-card {
  background-color: #f3f4f6;
  border-radius: 6px;
  padding: 12px;
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}

.stat-value {
  display: block;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.stat-value.success {
  color: #10b981;
}

.confidence-distribution {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.range-bar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.range-label {
  width: 60px;
  font-size: 12px;
  color: #6b7280;
  text-align: right;
}

.bar-container {
  flex: 1;
  height: 24px;
  background-color: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
}

.bar {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #1677ff);
  transition: width 0.3s ease;
}

.range-count {
  width: 40px;
  text-align: right;
  font-size: 12px;
  font-weight: 600;
  color: #1f2937;
}

.error-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
}

.error-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background-color: #fef2f2;
  border-left: 3px solid #ef4444;
  border-radius: 4px;
  font-size: 12px;
}

.error-index {
  font-weight: 600;
  color: #ef4444;
  min-width: 24px;
}

.error-input {
  flex: 1;
  color: #4b5563;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.error-reason {
  color: #9ca3af;
  font-size: 11px;
}

.classification-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.classification-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.category-name {
  width: 120px;
  font-size: 12px;
  color: #4b5563;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.category-bar {
  flex: 1;
  height: 20px;
  background-color: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
}

.category-fill {
  height: 100%;
  background: linear-gradient(90deg, #10b981, #059669);
  transition: width 0.3s ease;
}

.category-count {
  width: 40px;
  text-align: right;
  font-size: 12px;
  font-weight: 600;
  color: #1f2937;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .detail-content {
    padding: 12px;
  }
}
</style>

