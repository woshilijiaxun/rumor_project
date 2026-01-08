<template>
  <div class="settings-page">
    <div class="page-header">
      <h2>系统设置</h2>
      <p class="subtitle">根据角色显示不同的设置项；大部分为前端体验设置，默认保存在 localStorage。</p>
    </div>

    <!-- 1) 账号与安全（user/admin 都需要） -->
    <section class="card">
      <button class="card-header" type="button" @click="toggleSection('account')">
        <span class="card-title">账号与安全</span>
        <span class="chevron" :class="{ open: sectionOpen.account }">▾</span>
      </button>

      <div v-show="sectionOpen.account" class="grid">
        <div class="panel">
          <h4>个人资料</h4>
          <div class="form-row">
            <label>用户名</label>
            <input v-model.trim="profileForm.username" type="text" placeholder="至少3个字符" />
          </div>
          <div class="form-row">
            <label>邮箱</label>
            <input v-model.trim="profileForm.email" type="email" placeholder="可选" />
          </div>
          <div class="actions">
            <button class="btn btn-primary" :disabled="savingProfile" @click="saveProfile">保存资料</button>
          </div>
          <div v-if="profileMsg" class="msg">{{ profileMsg }}</div>
        </div>

        <div class="panel">
          <h4>修改密码</h4>
          <div class="form-row">
            <label>原密码</label>
            <input v-model="passwordForm.old_password" type="password" placeholder="请输入原密码" />
          </div>
          <div class="form-row">
            <label>新密码</label>
            <input v-model="passwordForm.new_password" type="password" placeholder="至少6位" />
          </div>
          <div class="actions">
            <button class="btn btn-primary" :disabled="savingPassword" @click="changePassword">修改密码</button>
          </div>
          <div v-if="passwordMsg" class="msg">{{ passwordMsg }}</div>
        </div>

        <div class="panel">
          <h4>登录设备 / 会话</h4>
          <div class="kv">
            <div class="kv-row">
              <span class="k">当前角色</span>
              <span class="v">{{ roleText }}</span>
            </div>
            <div class="kv-row">
              <span class="k">Token 过期时间</span>
              <span class="v">{{ tokenExpText }}</span>
            </div>
          </div>
          <div class="actions">
            <button class="btn btn-danger" @click="logoutAndClear">退出登录 / 清理本地缓存</button>
          </div>
        </div>
      </div>
    </section>

    <!-- 2) 文件与可见性默认策略（主要 user，部分 admin） -->
    <section class="card">
      <button class="card-header" type="button" @click="toggleSection('files')">
        <span class="card-title">文件与可见性默认策略</span>
        <span class="chevron" :class="{ open: sectionOpen.files }">▾</span>
      </button>
      <div v-show="sectionOpen.files" class="grid">
        <div class="panel">
          <h4>上传默认可见性</h4>
          <div class="form-row">
            <label>默认可见性</label>
            <select v-model="prefs.uploadDefaultVisibility">
              <option value="private">private（仅自己）</option>
              <option value="public">public（公开）</option>
            </select>
          </div>
          <p class="hint">仅影响前端上传时默认选项，不会修改已上传文件。</p>
        </div>

        <div class="panel">
          <h4>文件列表显示偏好</h4>
          <div class="form-row">
            <label>默认筛选</label>
            <select v-model="prefs.filesDefaultFilter">
              <option value="all">全部</option>
              <option value="public">仅 public</option>
              <option value="mine">仅我的</option>
            </select>
          </div>
          <div class="form-row">
            <label>每页条数</label>
            <select v-model.number="prefs.filesPageSize">
              <option :value="10">10</option>
              <option :value="20">20</option>
              <option :value="50">50</option>
            </select>
          </div>
        </div>
      </div>
    </section>

    <!-- 3) 识别任务相关设置（user/admin 都有价值） -->
    <section class="card">
      <button class="card-header" type="button" @click="toggleSection('ident')">
        <span class="card-title">识别任务相关设置</span>
        <span class="chevron" :class="{ open: sectionOpen.ident }">▾</span>
      </button>
      <div v-show="sectionOpen.ident" class="grid">
        <div class="panel">
          <h4>默认 Top-K</h4>
          <div class="form-row">
            <label>结果展示默认 Top-K</label>
            <select v-model.number="prefs.identDefaultTopK">
              <option :value="10">Top-10</option>
              <option :value="20">Top-20</option>
              <option :value="50">Top-50</option>
            </select>
          </div>
        </div>

        <div class="panel">
          <h4>默认网络可视化参数</h4>
          <div class="form-row">
            <label>max_edges 默认值</label>
            <select v-model.number="prefs.identDefaultMaxEdges">
              <option :value="10000">10k</option>
              <option :value="30000">30k</option>
            </select>
          </div>
          <div class="form-row">
            <label>默认“非Top-K置灰”</label>
            <select v-model="prefs.identDefaultNonTopKGray">
              <option value="0">否</option>
              <option value="1">是</option>
            </select>
          </div>
        </div>

        <div class="panel">
          <h4>任务轮询 / 超时策略（前端）</h4>
          <div class="form-row">
            <label>轮询间隔</label>
            <select v-model.number="prefs.identPollIntervalMs">
              <option :value="1000">1s</option>
              <option :value="2000">2s</option>
            </select>
          </div>
          <div class="form-row">
            <label>超时阈值</label>
            <select v-model.number="prefs.identPollTimeoutMs">
              <option :value="300000">5min</option>
              <option :value="600000">10min</option>
            </select>
          </div>
        </div>
      </div>
    </section>

    

    <div class="savebar">
      <button class="btn btn-secondary" @click="resetPrefs">恢复默认</button>
      <button class="btn btn-primary" @click="savePrefs">保存偏好设置</button>
      <span v-if="prefsMsg" class="msg inline">{{ prefsMsg }}</span>
    </div>
  </div>
</template>

<script>
import { computed, reactive, ref, onMounted } from 'vue'
import axios from 'axios'

const LS_KEY = 'app_settings'

const defaultPrefs = () => ({
  // 2) 文件
  uploadDefaultVisibility: 'private',
  filesDefaultFilter: 'all',
  filesPageSize: 20,

  // 3) 识别
  identDefaultTopK: 10,
  identDefaultMaxEdges: 10000,
  identDefaultNonTopKGray: '0',
  identPollIntervalMs: 1000,
  identPollTimeoutMs: 600000
})

function safeParseJwtExp(token) {
  try {
    const parts = String(token || '').split('.')
    if (parts.length < 2) return null
    const payloadStr = atob(parts[1].replace(/-/g, '+').replace(/_/g, '/'))
    const payload = JSON.parse(payloadStr)
    const exp = Number(payload?.exp)
    return Number.isFinite(exp) ? exp * 1000 : null
  } catch {
    return null
  }
}

export default {
  name: 'SettingsPage',
  setup() {
    const currentUser = ref(null)

    const isAdmin = computed(() => {
      const u = currentUser.value
      return u?.role === 'admin'
    })

    const roleText = computed(() => (isAdmin.value ? 'admin' : 'user'))

    const tokenExpText = computed(() => {
      const token = localStorage.getItem('token') || ''
      const expMs = safeParseJwtExp(token)
      if (!expMs) return '未知'
      const d = new Date(expMs)
      return d.toLocaleString('zh-CN')
    })

    // 折叠状态
    const sectionOpen = reactive({ account: false, files: false, ident: false, admin: false })
    const toggleSection = (key) => { sectionOpen[key] = !sectionOpen[key] }

    // 账号资料
    const profileForm = reactive({ username: '', email: '' })
    const passwordForm = reactive({ old_password: '', new_password: '' })
    const savingProfile = ref(false)
    const savingPassword = ref(false)
    const profileMsg = ref('')
    const passwordMsg = ref('')

    // 偏好设置（localStorage）
    const prefs = reactive(defaultPrefs())
    const prefsMsg = ref('')

    const loadUserFromLocalStorage = () => {
      try {
        currentUser.value = JSON.parse(localStorage.getItem('user') || 'null')
      } catch {
        currentUser.value = null
      }
      profileForm.username = currentUser.value?.username || ''
      profileForm.email = currentUser.value?.email || ''
    }

    const loadPrefs = () => {
      const base = defaultPrefs()
      try {
        const raw = localStorage.getItem(LS_KEY)
        if (!raw) {
          Object.assign(prefs, base)
          return
        }
        const v = JSON.parse(raw)
        Object.assign(prefs, base, v || {})
      } catch {
        Object.assign(prefs, base)
      }
    }

    const savePrefs = () => {
      prefsMsg.value = ''
      try {
        localStorage.setItem(LS_KEY, JSON.stringify({ ...prefs }))
        prefsMsg.value = '已保存'
      } catch (e) {
        prefsMsg.value = e?.message || '保存失败'
      }
      setTimeout(() => { prefsMsg.value = '' }, 1200)
    }

    const resetPrefs = () => {
      Object.assign(prefs, defaultPrefs())
      savePrefs()
    }

    const saveProfile = async () => {
      profileMsg.value = ''
      savingProfile.value = true
      try {
        const res = await axios.post('/api/users/update', {
          username: profileForm.username,
          email: profileForm.email
        })
        const updated = res?.data?.data || res?.data
        // 尽量兼容 ok() 返回结构
        if (updated && updated.username) {
          currentUser.value = { ...(currentUser.value || {}), ...updated }
          localStorage.setItem('user', JSON.stringify(currentUser.value))
        }
        profileMsg.value = '资料已更新'
      } catch (e) {
        profileMsg.value = e?.response?.data?.message || e?.message || '更新失败'
      } finally {
        savingProfile.value = false
        setTimeout(() => { profileMsg.value = '' }, 1500)
      }
    }

    const changePassword = async () => {
      passwordMsg.value = ''
      savingPassword.value = true
      try {
        await axios.post('/api/users/update', {
          old_password: passwordForm.old_password,
          new_password: passwordForm.new_password
        })
        passwordForm.old_password = ''
        passwordForm.new_password = ''
        passwordMsg.value = '密码已更新'
      } catch (e) {
        passwordMsg.value = e?.response?.data?.message || e?.message || '修改失败'
      } finally {
        savingPassword.value = false
        setTimeout(() => { passwordMsg.value = '' }, 1500)
      }
    }

    const logoutAndClear = () => {
      // 只清理与登录/偏好相关的本地缓存
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      localStorage.removeItem(LS_KEY)
      window.location.href = '/login'
    }

    onMounted(() => {
      loadUserFromLocalStorage()
      loadPrefs()
    })

    return {
      isAdmin,
      roleText,
      tokenExpText,
      profileForm,
      passwordForm,
      savingProfile,
      savingPassword,
      profileMsg,
      passwordMsg,
      prefs,
      prefsMsg,
      savePrefs,
      resetPrefs,
      saveProfile,
      changePassword,
      logoutAndClear,
      sectionOpen,
      toggleSection
    }
  }
}
</script>

<style scoped>
.settings-page {
  background: transparent;
}

.page-header {
  margin-bottom: 16px;
}

.page-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: #1f2937;
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
  font-weight: 700;
  color: #111827;
}

.chevron {
  font-size: 14px;
  color: #6b7280;
  transition: transform 0.18s ease;
  transform: rotate(-90deg); /* 默认收起 */
}

.chevron.open {
  transform: rotate(0deg);
}

.grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

@media (max-width: 1100px) {
  .grid { grid-template-columns: 1fr; }
}

.panel {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 12px;
  background: #fafafa;
}

.panel h4 {
  margin: 0 0 10px;
  font-size: 13px;
  font-weight: 700;
  color: #374151;
}

.form-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 10px;
}

.form-row label {
  font-size: 12px;
  color: #6b7280;
}

input, select {
  padding: 8px 10px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 13px;
  background: #fff;
}

input:focus, select:focus {
  outline: none;
  border-color: #1677ff;
  box-shadow: 0 0 0 2px rgba(22, 119, 255, 0.12);
}

.actions {
  display: flex;
  gap: 10px;
  margin-top: 8px;
}

.kv {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.kv-row {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  font-size: 13px;
}

.kv-row .k { color: #6b7280; }
.kv-row .v { color: #111827; font-weight: 600; }

.hint {
  margin: 0;
  font-size: 12px;
  color: #6b7280;
  line-height: 1.6;
}

.savebar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 0;
}

.btn {
  padding: 8px 12px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  font-size: 13px;
}

.btn-primary {
  background: #1677ff;
  color: #fff;
}

.btn-primary:disabled {
  background: #bfdbfe;
  cursor: not-allowed;
}

.btn-secondary {
  background: #e5e7eb;
  color: #374151;
}

.btn-danger {
  background: #ef4444;
  color: #fff;
}

.msg {
  margin-top: 10px;
  font-size: 12px;
  color: #065f46;
}

.msg.inline {
  margin: 0;
}
</style>
