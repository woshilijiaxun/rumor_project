<template>
  <div class="modal-overlay" @click.self="emitClose">
    <div class="modal-content">
      <div class="modal-header">
        <h3>识别历史</h3>
        <button class="modal-close" @click="emitClose">×</button>
      </div>

      <div class="modal-body">
        <TaskHistory
          :tasks="tasks"
          :total-pages="totalPages"
          :current-page="currentPage"
          :loading="loading"
          :error="error"
          :is-admin="isAdmin"
          :user-filter="userFilter"
          @set-user-filter="handleSetUserFilter"
          @refresh="refresh"
          @page-change="handlePageChange"
          @view-details="handleViewDetails"
          @delete="handleDelete"
        />
      </div>

      <div class="modal-footer">
        <button class="btn btn-secondary" @click="emitClose">关闭</button>
      </div>
    </div>
  </div>
</template>

<script>
import TaskHistory from './TaskHistory.vue'

export default {
  name: 'TaskHistoryModal',
  components: { TaskHistory },
  props: {
    tasks: { type: Array, default: () => [] },
    totalPages: { type: Number, default: 1 },
    currentPage: { type: Number, default: 1 },
    loading: { type: Boolean, default: false },
    error: { type: String, default: '' },
    isAdmin: { type: Boolean, default: false },
    userFilter: { type: [String, Number, null], default: null }
  },
  emits: ['close', 'refresh', 'page-change', 'view-details', 'delete', 'set-user-filter'],
  setup(_props, { emit }) {
    const emitClose = () => emit('close')
    const refresh = () => emit('refresh')
    const handlePageChange = (page) => emit('page-change', page)
    const handleViewDetails = (task) => emit('view-details', task)
    const handleDelete = (task) => emit('delete', task)
    const handleSetUserFilter = (v) => emit('set-user-filter', v)

    return {
      emitClose,
      refresh,
      handlePageChange,
      handleViewDetails,
      handleDelete,
      handleSetUserFilter
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1100;
}

.modal-content {
  background: white;
  border-radius: 10px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.18);
  width: 92%;
  max-width: 920px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  border: 1px solid #bfdbfe;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid #bfdbfe;
  background: linear-gradient(180deg, #eff6ff 0%, #ffffff 100%);
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1d4ed8;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  color: #6b7280;
  cursor: pointer;
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-close:hover {
  color: #111827;
}

.modal-body {
  padding: 16px;
  overflow: auto;
}

.modal-footer {
  padding: 12px 16px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: flex-end;
}

.btn {
  padding: 8px 14px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.btn-secondary {
  background-color: #e5e7eb;
  color: #374151;
}

.btn-secondary:hover {
  background-color: #d1d5db;
}
</style>
