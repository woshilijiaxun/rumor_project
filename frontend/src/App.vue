<template>
  <router-view></router-view>
</template>

<script>
export default {
  name: 'App'
}
</script>

  <style>
.refresh-btn,
.debunk-refresh {
  padding: 8px 16px;
  background: #fff;
  color: #374151;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease;
}

.refresh-btn:hover:not(:disabled),
.debunk-refresh:hover:not(:disabled) {
  background: #f5f7fa;
  border-color: #cbd5e1;
}

.refresh-btn:disabled,
.debunk-refresh:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
