<template>
  <div class="task-history">
    <div class="history-header">
      <h3>识别任务历史</h3>
      <div class="header-actions">
        <input 
          v-model="searchKeyword" 
          type="text" 
          placeholder="搜索任务..."
          class="search-input"
        />
        <button @click="refreshTasks" class="refresh-btn">刷新</button>
      </div>
    </div>

    <div class="history-content">
      <div v-if="filteredTasks.length === 0" class="empty-state">
        <p>暂无任务历史</p>
      </div>

      <div v-else class="tasks-list">
        <div v-for="task in filteredTasks" :key="task.id" class="task-item">
          <div class="task-info">
            <div class="task-title">{{ task.name }}</div>
            <div class="task-meta">
              <span class="meta-item">
                <span class="label">算法:</span>
                <span class="value">{{ task.algorithmName }}</span>
              </span>
              <span class="meta-item">
                <span class="label">时间:</span>
                <span class="value">{{ formatTime(task.createdAt) }}</span>
              </span>
              <span class="meta-item">
                <span class="label">数据量:</span>
                <span class="value">{{ task.dataCount }}</span>
              </span>
            </div>
          </div>

          <div class="task-stats">
            <div class="stat">
              <span class="stat-label">成功</span>
              <span class="stat-value success">{{ task.successCount }}</span>
            </div>
            <div class="stat">
              <span class="stat-label">失败</span>
              <span class="stat-value error">{{ task.failureCount }}</span>
            </div>
            <div class="stat">
              <span class="stat-label">置信度</span>
              <span class="stat-value">{{ task.avgConfidence }}</span>
            </div>
          </div>

          <div class="task-status">
            <span :class="['status-badge', task.status]">
              {{ getStatusText(task.status) }}
            </span>
          </div>

          <div class="task-actions">
            <button @click="viewDetails(task)" class="action-btn view-btn">查看</button>
            <button @click="downloadResults(task)" class="action-btn download-btn">下载</button>
            <button @click="deleteTask(task)" class="action-btn delete-btn">删除</button>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div v-if="totalPages > 1" class="pagination">
        <button 
          @click="previousPage" 
          :disabled="currentPage === 1"
          class="page-btn"
        >
          上一页
        </button>
        <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
        <button 
          @click="nextPage" 
          :disabled="currentPage === totalPages"
          class="page-btn"
        >
          下一页
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'

export default {
  name: 'TaskHistory',
  props: {
    tasks: {
      type: Array,
      default: () => []
    },
    totalPages: {
      type: Number,
      default: 1
    },
    currentPage: {
      type: Number,
      default: 1
    }
  },
  emits: ['view-details', 'download', 'delete', 'page-change', 'refresh'],
  setup(props, { emit }) {
    const searchKeyword = ref('')

    const filteredTasks = computed(() => {
      if (!searchKeyword.value) {
        return props.tasks
      }
      const keyword = searchKeyword.value.toLowerCase()
      return props.tasks.filter(task =>
        task.name.toLowerCase().includes(keyword) ||
        task.algorithmName.toLowerCase().includes(keyword)
      )
    })

    const formatTime = (timestamp) => {
      const date = new Date(timestamp)
      return date.toLocaleString('zh-CN')
    }

    const getStatusText = (status) => {
      const statusMap = {
        'completed': '已完成',
        'processing': '处理中',
        'failed': '失败',
        'cancelled': '已取消'
      }
      return statusMap[status] || status
    }

    const viewDetails = (task) => {
      emit('view-details', task)
    }

    const downloadResults = (task) => {
      emit('download', task)
    }

    const deleteTask = (task) => {
      if (confirm(`确定要删除任务 "${task.name}" 吗？`)) {
        emit('delete', task)
      }
    }

    const refreshTasks = () => {
      emit('refresh')
    }

    const previousPage = () => {
      if (props.currentPage > 1) {
        emit('page-change', props.currentPage - 1)
      }
    }

    const nextPage = () => {
      if (props.currentPage < props.totalPages) {
        emit('page-change', props.currentPage + 1)
      }
    }

    return {
      searchKeyword,
      filteredTasks,
      formatTime,
      getStatusText,
      viewDetails,
      downloadResults,
      deleteTask,
      refreshTasks,
      previousPage,
      nextPage
    }
  }
}
</script>

<style scoped>
.task-history {
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.history-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
  background-color: #f9fafb;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.history-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.search-input {
  padding: 6px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 13px;
  width: 200px;
}

.search-input:focus {
  outline: none;
  border-color: #1677ff;
  box-shadow: 0 0 0 2px rgba(22, 119, 255, 0.1);
}

.refresh-btn {
  padding: 6px 16px;
  background-color: #e5e7eb;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.refresh-btn:hover {
  background-color: #d1d5db;
}

.history-content {
  padding: 20px;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #9ca3af;
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background-color: #f9fafb;
  transition: all 0.3s;
}

.task-item:hover {
  background-color: #f3f4f6;
  border-color: #d1d5db;
}

.task-info {
  flex: 1;
  min-width: 0;
}

.task-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-meta {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  gap: 4px;
  font-size: 12px;
}

.meta-item .label {
  color: #6b7280;
}

.meta-item .value {
  color: #4b5563;
  font-weight: 500;
}

.task-stats {
  display: flex;
  gap: 16px;
  min-width: 150px;
}

.stat {
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 11px;
  color: #6b7280;
  margin-bottom: 2px;
}

.stat-value {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.stat-value.success {
  color: #10b981;
}

.stat-value.error {
  color: #ef4444;
}

.task-status {
  min-width: 80px;
}

.status-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  text-align: center;
  width: 100%;
}

.status-badge.completed {
  background-color: #d1fae5;
  color: #065f46;
}

.status-badge.processing {
  background-color: #fef3c7;
  color: #92400e;
}

.status-badge.failed {
  background-color: #fee2e2;
  color: #7f1d1d;
}

.status-badge.cancelled {
  background-color: #f3f4f6;
  color: #6b7280;
}

.task-actions {
  display: flex;
  gap: 8px;
  min-width: 180px;
}

.action-btn {
  flex: 1;
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s;
}

.view-btn {
  background-color: #1677ff;
  color: white;
}

.view-btn:hover {
  background-color: #0d5ccc;
}

.download-btn {
  background-color: #10b981;
  color: white;
}

.download-btn:hover {
  background-color: #059669;
}

.delete-btn {
  background-color: #ef4444;
  color: white;
}

.delete-btn:hover {
  background-color: #dc2626;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e5e7eb;
}

.page-btn {
  padding: 6px 16px;
  background-color: #e5e7eb;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.page-btn:hover:not(:disabled) {
  background-color: #d1d5db;
}

.page-btn:disabled {
  background-color: #f3f4f6;
  color: #9ca3af;
  cursor: not-allowed;
}

.page-info {
  font-size: 13px;
  color: #6b7280;
  min-width: 80px;
  text-align: center;
}

@media (max-width: 1024px) {
  .task-item {
    flex-wrap: wrap;
  }

  .task-info {
    width: 100%;
  }

  .task-stats {
    order: 3;
    width: 100%;
    margin-top: 8px;
  }

  .task-status {
    order: 2;
  }

  .task-actions {
    order: 4;
    width: 100%;
    margin-top: 8px;
  }
}

@media (max-width: 768px) {
  .history-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }

  .header-actions {
    width: 100%;
    flex-direction: column;
  }

  .search-input {
    width: 100%;
  }

  .task-meta {
    flex-direction: column;
    gap: 4px;
  }
}
</style>

