<template>
  <div class="algorithms-page">
    <div class="page-header">
      <h3>算法管理</h3>
      <div class="actions">
        <button type="button" class="btn-primary" @click="openCreate">新增算法</button>
        <button type="button" class="refresh-btn" @click="fetchAlgorithms">刷新</button>
      </div>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-if="error" class="error">{{ error }}</div>

    <div class="filter-bar">
      <input v-model="search" type="text" placeholder="搜索算法名称/描述..." class="search-input" />
    </div>

    <div v-if="!loading && !error" class="cards">
      <div v-for="a in displayAlgorithms" :key="a.id" class="algo-card">
        <div class="card-top">
          <div class="title-row">
            <h2 class="title">{{ a.name || '-' }}</h2>
            <span class="tag" :class="(a.status === 'active') ? 'ok' : 'off'">
              {{ (a.status === 'active') ? '启用' : '停用' }}
            </span>
          </div>
          <div class="meta">
            <span v-if="a.type" class="pill type" title="类型">{{ a.type }}</span>
            <span class="time">{{ formatDate(a.created_at) }}</span>
          </div>
        </div>

        <div class="card-bottom">
          <div class="info-actions">
            <button type="button" class="info-btn" @click="togglePanel(a.id, 'intro')">算法介绍</button>
            <button type="button" class="info-btn" @click="togglePanel(a.id, 'scene')">适用场景</button>
          </div>

          <div v-if="panelVisible(a.id, 'intro')" class="panel">
            <div class="panel-title">算法介绍</div>
            <div class="panel-content">{{ parseDescription(a.description || '').intro || '暂无内容' }}</div>
          </div>
          <div v-if="panelVisible(a.id, 'scene')" class="panel">
            <div class="panel-title">适用场景</div>
            <div class="panel-content">{{ parseDescription(a.description || '').scene || '暂无内容' }}</div>
          </div>
        </div>

        <div class="card-actions">
          <a href="javascript:void(0)" @click="openEdit(a)">编辑</a>
          <a href="javascript:void(0)" @click="toggleStatus(a)">{{ (a.status === 'active') ? '停用' : '启用' }}</a>
          <a href="javascript:void(0)" class="danger" @click="removeAlgorithm(a)">删除</a>
        </div>
      </div>

      <div v-if="algorithms.length === 0" class="empty-card">暂无算法</div>
    </div>

    <!-- 新增/编辑算法弹窗 -->
    <div v-show="modalVisible" class="modal-mask" @click.self="closeModal">
      <div class="modal-container">
        <h3 class="modal-title">{{ editing ? '编辑算法' : '新增算法' }}</h3>

        <div class="form-row">
          <label>算法名称</label>
          <input v-model="form.name" type="text" placeholder="请输入算法名称" />
        </div>

        <div class="form-row">
          <label>algo_key</label>
          <input v-model="form.algo_key" type="text" placeholder="唯一标识（系统内部使用），例如 degree_centrality" />
        </div>

        <div class="form-row">
          <label>类型</label>
          <input v-model="form.type" type="text" placeholder="例如 network / text / custom" />
        </div>

        <div class="form-row">
          <label>算法介绍</label>
          <textarea v-model="form.intro" rows="3" placeholder="请输入算法介绍"></textarea>
        </div>

        <div class="form-row">
          <label>适用场景</label>
          <textarea v-model="form.scene" rows="3" placeholder="请输入适用场景"></textarea>
        </div>

        <div class="form-row inline">
          <label>状态</label>
          <select v-model="form.status">
            <option value="active">启用</option>
            <option value="inactive">停用</option>
          </select>
        </div>

        <div v-if="formError" class="form-error">{{ formError }}</div>
        <div v-if="formSuccess" class="form-success">{{ formSuccess }}</div>

        <div class="actions">
          <button @click="closeModal" :disabled="submitting">取消</button>
          <button class="primary" @click="submit" :disabled="submitting">{{ submitting ? '提交中...' : '确定' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'AlgorithmsPage',
  data() {
    return {
      algorithms: [],
      loading: false,
      error: '',
      search: '',

      modalVisible: false,
      editing: false,
      submitting: false,
      formError: '',
      formSuccess: '',
      form: {
        id: null,
        name: '',
        algo_key: '',
        type: '',
        intro: '',
        scene: '',
        status: 'active'
      },

      // 记录每个算法卡片下方展开的面板（intro/scene）
      expanded: {}
    }
  },
  computed: {
    displayAlgorithms() {
      const kw = (this.search || '').trim().toLowerCase()
      if (!kw) return this.algorithms
      return this.algorithms.filter(a => {
        const name = (a.name || '').toLowerCase()
        const desc = (a.description || '').toLowerCase()
        const type = (a.type || '').toLowerCase()
        return name.includes(kw) || desc.includes(kw) || type.includes(kw)
      })
    }
  },
  methods: {
    fetchAlgorithms() {
      this.loading = true
      this.error = ''

      const guard = setTimeout(() => {
        if (this.loading) {
          this.loading = false
          this.error = '加载超时，请点击刷新重试'
        }
      }, 8000)

      axios.get('/api/algorithms', { params: { page: 1, page_size: 100 } })
        .then(res => {
          clearTimeout(guard)
          // 后端返回：{status:'success', data:{items,total,page,page_size}}
          const d = res.data
          const items = d?.data?.items
          if (d?.status === 'success' && Array.isArray(items)) {
            this.algorithms = items
          } else {
            this.algorithms = []
            this.error = d?.message || '返回数据格式不符合预期'
          }
          this.loading = false
        })
        .catch(err => {
          clearTimeout(guard)
          this.error = err.response?.data?.message || err.message || '获取算法列表失败'
          this.algorithms = []
          this.loading = false
        })
    },

    openCreate() {
      this.editing = false
      this.form = { id: null, name: '', algo_key: '', type: '', intro: '', scene: '', status: 'active' }
      this.formError = ''
      this.formSuccess = ''
      this.modalVisible = true
    },
    openEdit(a) {
      this.editing = true
      const parsed = this.parseDescription(a.description || '')
      this.form = {
        id: a.id ?? null,
        name: a.name || '',
        algo_key: a.algo_key || '',
        type: a.type || '',
        intro: parsed.intro,
        scene: parsed.scene,
        status: a.status || 'active'
      }
      this.formError = ''
      this.formSuccess = ''
      this.modalVisible = true
    },
    closeModal() {
      if (this.submitting) return
      this.modalVisible = false
    },

    validate() {
      if (!this.form.name || !this.form.name.trim()) return '请输入算法名称'
      if (this.form.name.trim().length > 64) return '算法名称过长'
      if (!this.form.algo_key || !this.form.algo_key.trim()) return '请输入 algo_key'
      if (this.form.algo_key.trim().length > 64) return 'algo_key 过长'
      if (this.form.type && this.form.type.length > 64) return '类型过长'
      if (this.form.intro && this.form.intro.length > 2000) return '算法介绍过长'
      if (this.form.scene && this.form.scene.length > 2000) return '适用场景过长'
      if (!['active', 'inactive'].includes(this.form.status)) return '状态不合法'
      return ''
    },

    submit() {
      const msg = this.validate()
      if (msg) { this.formError = msg; return }

      this.submitting = true
      this.formError = ''
      this.formSuccess = ''

      const payload = {
        name: this.form.name.trim(),
        algo_key: (this.form.algo_key || '').trim(),
        type: (this.form.type || '').trim(),
        description: this.buildDescription(this.form.intro, this.form.scene),
        status: this.form.status || 'active'
      }

      const req = this.editing
        ? axios.put(`/api/algorithms/${this.form.id}`, payload)
        : axios.post('/api/algorithms', payload)

      req.then(res => {
        if (res.data?.status && res.data.status !== 'success') {
          this.formError = res.data?.message || '操作失败'
          return
        }
        this.formSuccess = this.editing ? '保存成功' : '创建成功'
        setTimeout(() => {
          this.modalVisible = false
          this.fetchAlgorithms()
        }, 400)
      }).catch(err => {
        this.formError = err.response?.data?.message || err.message || '操作失败'
      }).finally(() => {
        this.submitting = false
      })
    },

    toggleStatus(a) {
      const nextStatus = (a.status === 'active') ? 'inactive' : 'active'
      const tip = nextStatus === 'active' ? '确认启用该算法？' : '确认停用该算法？'
      if (!confirm(tip)) return

      const id = a.id
      axios.put(`/api/algorithms/${id}`, { status: nextStatus })
        .then(res => {
          if (res.data?.status && res.data.status !== 'success') {
            alert(res.data?.message || '更新失败')
            return
          }
          a.status = nextStatus
        })
        .catch(err => alert(err.response?.data?.message || err.message || '更新失败'))
    },

    removeAlgorithm(a) {
      const name = a.name || ''
      if (!confirm(`确认删除算法: ${name} ?`)) return
      axios.delete(`/api/algorithms/${a.id}`)
        .then(res => {
          if (res.data?.status && res.data.status !== 'success') {
            alert(res.data?.message || '删除失败')
          } else {
            this.fetchAlgorithms()
          }
        })
        .catch(err => alert(err.response?.data?.message || err.message || '删除失败'))
    },

    buildDescription(intro, scene) {
      const introText = (intro || '').trim()
      const sceneText = (scene || '').trim()
      // 采用明确分隔符，便于后续从 description 里再解析出来
      // 兼容老数据：若解析不到，则 intro=原description, scene=''
      return `【算法介绍】\n${introText}\n\n【适用场景】\n${sceneText}`.trim()
    },
    parseDescription(description) {
      const raw = String(description || '')
      const introTag = '【算法介绍】'
      const sceneTag = '【适用场景】'

      const i1 = raw.indexOf(introTag)
      const i2 = raw.indexOf(sceneTag)

      // 新格式
      if (i1 !== -1 && i2 !== -1 && i2 > i1) {
        const introPart = raw.slice(i1 + introTag.length, i2).trim()
        const scenePart = raw.slice(i2 + sceneTag.length).trim()
        return { intro: introPart, scene: scenePart }
      }

      // 兼容：只有介绍
      if (i1 !== -1 && i2 === -1) {
        const introPart = raw.slice(i1 + introTag.length).trim()
        return { intro: introPart, scene: '' }
      }

      // 兼容：只有场景
      if (i1 === -1 && i2 !== -1) {
        const scenePart = raw.slice(i2 + sceneTag.length).trim()
        return { intro: '', scene: scenePart }
      }

      // 老数据：没有标记，全部当作“算法介绍”
      return { intro: raw.trim(), scene: '' }
    },

    panelVisible(id, which) {
      const key = String(id)
      return this.expanded[key] === which
    },
    togglePanel(id, which) {
      const key = String(id)
      const cur = this.expanded[key] || ''
      // Vue3 不需要 $set，这里做兼容写法
      this.expanded[key] = (cur === which ? '' : which)
    },

    formatDate(v) {
      if (!v) return '-'
      const t = Date.parse(v)
      if (isNaN(t)) return String(v)
      return new Date(t).toLocaleString('zh-CN')
    }
  },
  mounted() {
    this.fetchAlgorithms()
  }
}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h3 { margin: 0; color: #333; }
.actions { display: flex; align-items: center; gap: 10px; }

.btn-primary { padding: 8px 16px; background: #1677ff; color: #fff; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600; }
.btn-primary:hover { background: #4096ff; }

.loading, .error { text-align: left; padding: 8px 0; color: #666; }
.error { color: #d32f2f; }

/* 卡片列表 */
.cards { display: grid; grid-template-columns: repeat(1, minmax(0, 1fr)); gap: 14px; }

.algo-card {
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid #eef0f3;
  border-radius: 14px;
  padding: 16px 16px 12px;
  box-shadow: 0 10px 24px rgba(0,0,0,.06);
  backdrop-filter: blur(2px);
}

.card-top { margin-bottom: 10px; }
.title-row { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; }
.title { margin: 0; font-size: 22px; line-height: 1.2; font-weight: 800; color: #222; letter-spacing: .2px; }

.meta { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-top: 10px; }
.pill { display: inline-flex; align-items: center; padding: 6px 10px; border-radius: 10px; background: #fff; border: 1px solid #e5e7eb; font-size: 13px; color: #444; max-width: 100%; }
.pill.type { background: #f6ffed; border-color: #b7eb8f; color: #237804; }
.time { color: #999; font-size: 13px; }

.card-bottom { margin: 8px 0 12px; }

.info-actions { display: flex; gap: 10px; flex-wrap: wrap; }
.info-btn {
  padding: 8px 14px;
  border-radius: 10px;
  border: 1px solid #dcdfe6;
  background: #fff;
  color: #333;
  cursor: pointer;
  font-weight: 700;
}
.info-btn:hover { border-color: #1677ff; color: #1677ff; box-shadow: 0 0 0 2px rgba(22,119,255,.10); }

.panel { margin-top: 10px; border: 1px solid #eef0f3; border-radius: 12px; background: #fafafa; padding: 12px; }
.panel-title { font-weight: 800; color: #333; margin-bottom: 6px; }
.panel-content { color: #8b8b8b; font-size: 15px; line-height: 1.7; white-space: pre-wrap; }

.card-actions { display: flex; gap: 14px; justify-content: flex-end; border-top: 1px solid #f0f0f0; padding-top: 10px; }
.card-actions a { color: #1890ff; text-decoration: none; cursor: pointer; font-weight: 600; }
.card-actions a:hover { text-decoration: underline; color: #40a9ff; }
.card-actions a.danger { color: #d32f2f; }
.card-actions a.danger:hover { color: #b71c1c; }

.empty-card { text-align: center; color: #999; padding: 40px; border: 1px dashed #e5e7eb; border-radius: 12px; background: #fafafa; }

/* 搜索栏（FilesPage 里有注释“与算法管理页面风格一致”，因此这里定义为基准） */
.filter-bar { display: flex; gap: 10px; margin: 10px 0 12px; }
.search-input { padding: 8px 12px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 14px; width: 320px; }
.search-input:focus { outline: none; border-color: #1677ff; box-shadow: 0 0 0 2px rgba(22,119,255,.15); }

.tag { display: inline-flex; align-items: center; padding: 2px 10px; border-radius: 999px; font-size: 12px; border: 1px solid transparent; }
.tag.ok { color: #1f7a1f; background: #f0fff0; border-color: #b7eb8f; }
.tag.off { color: #8a5a00; background: #fff7e6; border-color: #ffd591; }

/* 弹窗样式（与 FilesPage 保持一致） */
.modal-mask { position: fixed; z-index: 4000; inset: 0; background: rgba(0,0,0,.35); display: flex; align-items: center; justify-content: center; padding: 20px; }
.modal-container { width: 460px; max-width: 92vw; background: #fff; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,.15); padding: 20px; }
.modal-title { margin: 0 0 12px; font-size: 18px; font-weight: 700; color: #333; }
.form-row { display: flex; flex-direction: column; gap: 6px; margin-bottom: 12px; }
.form-row.inline { flex-direction: row; align-items: center; gap: 10px; }
.form-row label { font-size: 13px; color: #666; min-width: 60px; }
.form-row input, .form-row textarea, .form-row select { padding: 8px 10px; border: 1px solid #dcdfe6; border-radius: 8px; font-size: 14px; outline: none; }
.form-row input:focus, .form-row textarea:focus, .form-row select:focus { border-color: #1677ff; box-shadow: 0 0 0 2px rgba(22,119,255,.15); }
.form-error { color: #d93025; margin: 6px 0; }
.form-success { color: #2e7d32; margin: 6px 0; }
.actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 8px; }
.actions button { padding: 8px 14px; border: 1px solid #dcdfe6; background: #fff; color: #333; border-radius: 6px; cursor: pointer; }
.actions button.primary { background: #1890ff; border-color: #1890ff; color: #fff; }
.actions button:disabled { opacity: .6; cursor: not-allowed; }
</style>

