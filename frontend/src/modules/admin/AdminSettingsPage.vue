<template>
  <div class="admin-settings-page">
    <div class="page-header">
      <h2>管理员设置</h2>
      <p class="subtitle">系统级配置与审计，仅管理员可见。</p>
    </div>

    <section class="card">
      <button class="card-header" type="button" @click="toggle('config')">
        <span class="card-title">系统配置</span>
        <span class="chevron" :class="{ open: openMap.config }">▾</span>
      </button>

      <div v-show="openMap.config" class="card-body">
        <p class="hint">即将支持：default_algorithm_key、max_upload_mb、max_edges_limit、模块开关等（由后端 system_config 提供）。</p>
        <button class="btn btn-secondary" disabled>加载配置（待后端接口）</button>
      </div>
    </section>

    <section class="card">
      <button class="card-header" type="button" @click="toggle('algo')">
        <span class="card-title">算法启用 / 停用</span>
        <span class="chevron" :class="{ open: openMap.algo }">▾</span>
      </button>

      <div v-show="openMap.algo" class="card-body">
        <p class="hint">即将支持：对 algorithms.status 进行集中管理。</p>
        <button class="btn btn-secondary" disabled>加载算法列表（待接入）</button>
      </div>
    </section>

    <section class="card">
      <button class="card-header" type="button" @click="toggle('audit')">
        <span class="card-title">审计日志</span>
        <span class="chevron" :class="{ open: openMap.audit }">▾</span>
      </button>

      <div v-show="openMap.audit" class="card-body">
        <p class="hint">即将支持：查看管理员关键操作日志（配置变更、启停算法、删除文件/任务等）。</p>
        <button class="btn btn-secondary" disabled>查询日志（待后端接口）</button>
      </div>
    </section>

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
import { reactive } from 'vue'

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
    }

    return { openMap, toggle }
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

.btn {
  padding: 8px 12px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  font-size: 13px;
}

.btn-secondary {
  background: #e5e7eb;
  color: #374151;
}
</style>

