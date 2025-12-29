<template>
  <div v-if="visible" class="modal-overlay" @click.self="onClose">
    <div class="modal-content">
      <div class="modal-header">
        <h3>操作失败</h3>
        <button class="modal-close" @click="onClose">×</button>
      </div>
      <div class="modal-body">
        <p class="message">{{ message }}</p>
        <p v-if="detail" class="detail">{{ detail }}</p>
      </div>
      <div class="modal-footer">
        <button class="btn btn-primary" @click="onClose">我知道了</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ErrorModal',
  props: {
    visible: { type: Boolean, default: false },
    message: { type: String, default: '' },
    detail: { type: String, default: '' }
  },
  emits: ['close'],
  setup(props, { emit }) {
    const onClose = () => emit('close')
    return { onClose }
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
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  width: 90%;
  max-width: 520px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  animation: slideIn 0.2s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-12px);
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
  padding: 14px 16px;
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
}

.modal-body {
  padding: 16px;
}

.message {
  margin: 0;
  font-size: 14px;
  color: #374151;
  line-height: 1.5;
  word-break: break-word;
}

.detail {
  margin: 10px 0 0 0;
  font-size: 12px;
  color: #6b7280;
  word-break: break-word;
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
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
}

.btn-primary {
  background-color: #1677ff;
  color: white;
}

.btn-primary:hover {
  background-color: #0d5ccc;
}
</style>

