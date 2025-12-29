<template>
  <div class="admin-layout">
    <aside class="sidebar">
      <div class="logo">谣言关键传播者<br></br>识别系统</div>
      
      <nav>
        <ul>
          <li @click="go('dashboard')" :class="{ active: activeMenu === 'dashboard' }">首页</li>
          <li @click="go('users')" :class="{ active: activeMenu === 'users' }">用户管理</li>
          <li @click="go('files')" :class="{ active: activeMenu === 'files' }">文件管理</li>
          <li @click="go('settings')" :class="{ active: activeMenu === 'settings' }">系统设置</li>

        </ul>
      </nav>
    </aside>

    <div class="main-content">
      <header>
        <h1>{{ pageTitle }}</h1>
        <div class="header-right">
          <div class="user-menu" @mouseenter="openMenu" @mouseleave="closeMenu" @click="toggleMenu" ref="userMenu">
            <span class="user-name">{{ currentUser ? currentUser.username : '未登录' }}</span>
            <span class="caret">▾</span>
            <div class="dropdown" v-show="menuOpen" @click.stop>
              <div class="dropdown-item" @click="openEdit">修改账号/密码</div>
              <div class="dropdown-item danger" @click="logout">退出登录</div>
            </div>
          </div>
        </div>
      </header>

      <section class="content">
        <!-- 首页 -->
        <div v-if="activeMenu === 'dashboard'" class="home">
          <div class="home-hero">
            <h2>谣言传播的危害</h2>
            <p>
              
              为深入清理网络谣言和虚假信息，营造风清气正的网络环境，按照2022年
              <a href="https://www.cac.gov.cn/2022-09/02/c_1663745754062601.htm?eqid=acc86064002cc5cf000000046455bb75" title="访问示例网站了解更多" target="_blank">“清朗”系列专项行动总体安排</a>
              中央网信办决定即日起在全国范围内启动为期3个月的“清朗·打击网络谣言和虚假信息”专项行动。
              在2025年9月，<a href="https://www.cac.gov.cn/2025-09/22/c_1760258688713582.htm" title="访问示例网站了解更多" target="_blank">中央网信办继续深化了“清朗”系列活动</a>，这充分说明了该问题的紧迫性和长期性。            
            </p>
            <p>
              谣言在社交网络与即时通讯工具中极易扩散，会造成社会恐慌、破坏信任、影响公共决策，甚至引发经济损失与公共安全事件。
              因此尽早、准确的识别谣言关键传播者不仅能够帮助平台和监管机构采取干预措施，减少谣言的影响，还能够优化信息管控策略，从源头上遏制虚假信息的传播，提升平台的治理能力和社会稳定性。
              本系统旨在辅助识别关键传播者，帮助管理者更高效地遏制谣言扩散。
            </p>
          </div>


          <!-- 轮播图 -->
          <div class="carousel" @mouseenter="stopCarousel" @mouseleave="startCarousel">
            <div class="carousel-track" :style="{ transform: 'translateX(-' + (carouselIndex * 100) + '%)' }">
              <div class="carousel-slide" v-for="(group, i) in carouselSlides" :key="i">
                <div class="multi-slide">
                  <div class="tile" v-for="(img, j) in group" :key="j">
                    <img :src="img.src" :alt="img.alt || ('图' + (i*3 + j + 1))" loading="lazy" />
                  </div>
                </div>
              </div>
            </div>
            <button class="nav prev" @click="prevSlide">‹</button>
            <button class="nav next" @click="nextSlide">›</button>
            <div class="dots">
              <span v-for="(group, i) in carouselSlides" :key="i" :class="{ active: i === carouselIndex }" @click="goSlide(i)"></span>
            </div>
          </div>

          <!-- 危害卡片 -->
          <div class="home-cards">
            <div class="card">
              <h3>社会层面</h3>
              <p>制造公众恐慌与分裂，削弱社会凝聚力，放大刻板印象与对立情绪。</p>
            </div>
            <div class="card">
              <h3>治理层面</h3>
              <p>干扰决策与应急响应，造成资源错配，增加监管与辟谣的治理成本。</p>
            </div>
            <div class="card">
              <h3>个体层面</h3>
              <p>误导健康与财务选择，引发隐私泄露与网络暴力，伤害个人名誉与权益。</p>
            </div>
          </div>

          <!-- 典型影响（优化为卡片网格） -->
          <div class="impact-section">
            <h3>典型影响</h3>
            <div class="impact-grid">
              <div class="impact-card" v-for="it in impacts" :key="it.title">
                <div class="impact-badge"></div>
                <h4 class="impact-title">{{ it.title }}</h4>
                <p class="impact-desc">{{ it.desc }}</p>
              </div>
            </div>
          </div>

          <!-- 快捷入口 -->
          <div class="entry-cards">
            <div class="entry" @click="go('users')">
              <h4>进入用户管理</h4>
              <p>查看用户、刷新列表</p>
            </div>
            <div class="entry" @click="go('files')">
              <h4>文件管理</h4>
              <p>上传、预览、下载与删除文件</p>
            </div>
            <div class="entry" @click="go('settings')">
              <h4>系统设置</h4>
              <p>管理系统配置</p>
            </div>
      </div>
            <!-- 底部统计 -->
            <div class="stats stats-bottom">
              <div class="stat-card">
                <div class="stat-value">{{ statsLoading ? '...' : (stats?.users_total ?? 0) }}</div>
                <div class="stat-label">用户总数</div>
              </div>
              <div class="stat-card">
                <div class="stat-value">{{ statsLoading ? '...' : formatDate(stats?.latest_user_created_at) }}</div>
                <div class="stat-label">最近注册时间</div>
              </div>
            </div>
    </div>

        <!-- 用户管理 -->
        <div v-else-if="activeMenu === 'users'" class="users-page">
      <div class="page-header">
        <h3>用户列表</h3>
        <button @click="fetchUsers" class="refresh-btn">刷新</button>
      </div>
      <div v-if="loading" class="loading">加载中...</div>
      <div v-if="error" class="error">{{ error }}</div>
      <table v-if="!loading && !error" class="users-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>用户名</th>
            <th>邮箱</th>
            <th>注册时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.id }}</td>
            <td>{{ user.username }}</td>
            <td>{{ user.email || '-' }}</td>
                <td>{{ formatDateMs(user.created_at_ms) || formatDate(user.created_at) }}</td>
          </tr>
          <tr v-if="users.length === 0">
            <td colspan="4" class="empty">暂无用户数据</td>
          </tr>
        </tbody>
      </table>
    </div>

        <!-- 文件管理 -->
        <div v-else-if="activeMenu === 'files'" class="files-page">
          <div class="page-header">
            <h3>文件管理</h3>
            <div class="file-actions">
              <button type="button" class="btn-upload" @click="openUpload">
                <svg class="icon" width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                  <path d="M12 16V4M12 4l-4 4M12 4l4 4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M4 16v3a1 1 0 001 1h14a1 1 0 001-1v-3" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                上传文件
              </button>
              <button type="button" class="refresh-btn" @click="fetchFiles">刷新</button>
            </div>
          </div>

          <div class="list-header"></div>

          <div v-if="filesLoading" class="loading">加载中...</div>
          <div v-if="filesError" class="error">{{ filesError }}</div>
          <table v-if="!filesLoading && !filesError" class="users-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>文件名</th>
                <th>类型</th>
                <th>大小</th>
                <th>上传时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="f in files" :key="f.id">
                <td>{{ f.id }}</td>
                <td :title="f.original_name">{{ f.original_name }}</td>
                <td>{{ f.mime_type || '-' }}</td>
                <td>{{ formatSize(f.size_bytes) }}</td>
                <td>{{ formatDate(f.created_at) }}</td>
                <td class="ops">
                  <a href="javascript:void(0)" @click="previewFile(f)">预览</a>
                  <a href="javascript:void(0)" @click="downloadFile(f)">下载</a>
                  <a href="javascript:void(0)" @click="removeFile(f)">删除</a>
                </td>
              </tr>
              <tr v-if="files.length === 0">
                <td colspan="6" class="empty">暂无文件</td>
              </tr>
            </tbody>
          </table>

          <div class="pagination" v-if="total > page_size">
            <button :disabled="page<=1" @click="changePage(page-1)">上一页</button>
            <span>第 {{ page }} / {{ Math.ceil(total / page_size) }} 页</span>
            <button :disabled="page>=Math.ceil(total / page_size)" @click="changePage(page+1)">下一页</button>
          </div>
        </div>

        <!-- 系统设置 -->
        <div v-else-if="activeMenu === 'settings'" class="settings">
      <h3>系统设置</h3>
      <p>系统设置功能待开发...</p>
        </div>

        <!-- 兜底 -->
        <div v-else>页面不存在</div>
      </section>

      <!-- 编辑资料弹窗 -->
      <div v-if="editVisible" class="modal-mask" @click.self="closeEdit">
        <div class="modal-container">
          <h3 class="modal-title">编辑个人信息</h3>

          <div class="form-row">
            <label>用户名</label>
            <input v-model="editForm.username" placeholder="至少3个字符" />
          </div>
          <div class="form-row">
            <label>邮箱</label>
            <input v-model="editForm.email" type="email" placeholder="可选" />
          </div>

          <div class="divider"></div>

          <div class="form-row">
            <label>原密码</label>
            <input v-model="editForm.old_password" type="password" placeholder="修改密码时需填写" />
          </div>
          <div class="form-row">
            <label>新密码</label>
            <input v-model="editForm.new_password" type="password" placeholder="留空则不修改" />
          </div>
          <div class="form-row">
            <label>确认新密码</label>
            <input v-model="editForm.confirm_password" type="password" placeholder="重复新密码" />
          </div>

          <p v-if="editError" class="form-error">{{ editError }}</p>
          <p v-if="editSuccess" class="form-success">{{ editSuccess }}</p>

          <div class="actions">
            <button @click="closeEdit" :disabled="editSubmitting">取消</button>
            <button class="primary" @click="submitEdit" :disabled="editSubmitting">{{ editSubmitting ? '保存中...' : '保存' }}</button>
          </div>
        </div>
      </div>
      <!-- 上传文件弹窗 -->
      <div v-show="uploadVisible" class="modal-mask" @click.self="closeUpload">
        <div class="modal-container upload-modal">
          <h3 class="modal-title">上传文件</h3>
          <p class="hint">请选择要上传的文件，支持常见图片、文档与压缩包。单文件上限 20MB。</p>

          <div class="form-row file-chooser">
            <input id="uploadFileInput" type="file" @change="onFileChange" ref="fileInput" style="display:none" accept="*/*" />
            <button type="button" class="choose-btn" @click="chooseFile">选择文件</button>
            <span v-if="uploadFile" class="file-chip" :title="uploadFile.name">{{ uploadFile.name }}（{{ formatSize(uploadFile.size) }}）</span>
            <span v-else class="file-chip empty">未选择文件</span>
          </div>

          <div v-if="uploadError" class="form-error">{{ uploadError }}</div>
          <div v-if="uploadSuccess" class="form-success">{{ uploadSuccess }}</div>

          <div v-if="uploading" class="progress"><div class="bar" :style="{ width: uploadProgress + '%' }"></div></div>

          <div class="actions">
            <button @click="closeUpload" :disabled="uploading">取消</button>
            <button class="primary" @click="doUpload" :disabled="!uploadFile || uploading">{{ uploading ? '上传中...' : '开始上传' }}</button>
          </div>
        </div>
      </div>

      <!-- 上传结果确认弹窗 -->
      <div v-if="uploadResultVisible" class="modal-mask result-mask" @click.self="confirmUploadResult">
        <div class="modal-container result-modal">
          <h3 class="modal-title">提示</h3>
          <p style="margin: 8px 0 16px; color:#333;">{{ uploadResultMessage || '文件上传成功' }}</p>
          <div class="actions">
            <button class="primary" @click="confirmUploadResult">确定</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  data() {
    return {
      activeMenu: 'dashboard',
      // 用户列表模块
      users: [],
      loading: false,
      error: '',
      // 登录用户与菜单
      currentUser: null,
      menuOpen: false,
      // 首页统计
      stats: null,
      statsLoading: false,
      statsError: '',
      // 轮播
      carouselIndex: 0,
      carouselTimer: null,
      carouselImages: [
        { src: '/images/rumor1.JPG',  alt: '谣言治理图1', caption: '关键传播者识别' },
        { src: '/images/rumor2.jpg',  alt: '谣言治理图2', caption: '传播路径可视化' },
        { src: '/images/rumor3.jpeg', alt: '谣言治理图3', caption: '风险预警与干预' },
        { src: '/images/rumor4.webp', alt: '谣言治理图4', caption: '多源数据融合' },
        { src: '/images/rumor5.png',  alt: '谣言治理图5', caption: '全流程治理闭环' },
        { src: '/images/rumor6.png',  alt: '谣言治理图6', caption: '多方协同治理' }
      ],
      // 典型影响数据（用于卡片网格展示）
      impacts: [
        { title: '社会情绪与行为', desc: '公共事件期间引发情绪失控与囤积行为，扰乱供应链并造成价格波动。' },
        { title: '健康与安全误导', desc: '医疗与安全谣言使公众延误正确处置与求助，扩大事件影响范围。' },
        { title: '机构与企业声誉', desc: '谣言冲击组织信任与品牌形象，带来长期声誉风险与经济损失。' },
        { title: '政策与治理成本', desc: '干扰公共决策，导致资源错配，提升辟谣澄清的治理成本。' },
        { title: '个人权益与隐私', desc: '隐私泄露与网络暴力增多，个人名誉与心理健康受到伤害。' },
        { title: '平台生态与合规', desc: '平台生态恶化、合规压力上升，需强化风控与内容治理能力。' }
      ],
      // 文件管理
      uploadVisible: false,
      uploadFile: null,
      uploading: false,
      uploadProgress: 0,
      uploadError: '',
      uploadSuccess: '',
      uploadResultVisible: false,
      uploadResultMessage: '',
      files: [],
      filesLoading: false,
      filesError: '',
      page: 1,
      page_size: 10,
      total: 0,
      // 编辑弹窗
      editVisible: false,
      editSubmitting: false,
      editError: '',
      editSuccess: '',
      editForm: { id: null, username: '', email: '', old_password: '', new_password: '', confirm_password: '' }
    }
  },
  computed: {
    pageTitle() {
      switch (this.activeMenu) {
        case 'dashboard': return '首页'
        case 'users': return '用户管理'
        case 'files': return '文件管理'
        case 'settings': return '系统设置'
        default: return ''
      }
    },
    // 将图片按3张一组分组，供轮播每屏展示3张
    carouselSlides() {
      const size = 3
      const arr = this.carouselImages || []
      const groups = []
      for (let i = 0; i < arr.length; i += size) {
        groups.push(arr.slice(i, i + size))
      }
      return groups
    }
  },
  methods: {
    // 导航
    go(menu) {
      this.activeMenu = menu
      if (menu === 'users') {
        this.fetchUsers()
      }
      if (menu === 'dashboard') {
        this.fetchStats()
        this.startCarousel()
      } else {
        this.stopCarousel()
      }
      if (menu === 'files') {
        this.page = 1
        this.fetchFiles()
      }
    },

    // 用户列表
    fetchUsers() {
      this.loading = true
      this.error = ''
      axios.get('/api/users')
        .then(response => {
          const rows = Array.isArray(response.data) ? response.data : response.data?.data
          if (Array.isArray(rows)) {
            this.users = rows
          } else if (response.data?.status === 'success' && Array.isArray(response.data?.data)) {
            this.users = response.data.data
          } else {
            this.error = '返回数据格式不符合预期'
          }
        })
        .catch(error => {
          this.error = '获取用户列表失败: ' + (error.response?.data?.message || error.message)
        })
        .finally(() => {
          this.loading = false
        })
    },

    // 首页统计
    fetchStats() {
      this.statsLoading = true
      this.statsError = ''
      axios.get('/api/stats')
        .then(res => {
          if (res.data?.status === 'success') {
            this.stats = res.data.data || null
          } else {
            this.statsError = res.data?.message || '获取统计失败'
          }
        })
        .catch(err => {
          this.statsError = err.response?.data?.message || err.message || '获取统计失败'
        })
        .finally(() => {
          this.statsLoading = false
        })
    },

    // 轮播
    startCarousel() {
      this.stopCarousel()
      this.carouselTimer = setInterval(() => { this.nextSlide() }, 5000)
    },
    stopCarousel() {
      if (this.carouselTimer) { clearInterval(this.carouselTimer); this.carouselTimer = null }
    },
    nextSlide() {
      const n = this.carouselSlides.length
      if (!n) return
      this.carouselIndex = (this.carouselIndex + 1) % n
    },
    prevSlide() {
      const n = this.carouselSlides.length
      if (!n) return
      this.carouselIndex = (this.carouselIndex - 1 + n) % n
    },
    goSlide(i) { if (i >= 0 && i < this.carouselSlides.length) this.carouselIndex = i },

    // 选择文件按钮
    chooseFile() {
      const input = this.$refs.fileInput
      if (input) {
        input.click()
      }
    },

    // 文件管理
    openUpload() {
      this.uploadVisible = true
      this.uploadFile = null
      this.uploadError = ''
      this.uploadSuccess = ''
      this.uploadProgress = 0
    },
    closeUpload() {
      this.uploadVisible = false
    },
    onFileChange(e) {
      const f = e.target.files && e.target.files[0]
      this.uploadFile = f || null
      this.uploadError = ''
      this.uploadSuccess = ''
      this.uploadProgress = 0
    },
    doUpload() {
      if (!this.uploadFile) { this.uploadError = '请先选择文件'; return }
      
      // 验证文件大小 (20MB)
      if (this.uploadFile.size > 20 * 1024 * 1024) {
        this.uploadError = '文件大小不能超过 20MB'
        return
      }
      
      this.uploadError = ''
      this.uploadSuccess = ''
      const fd = new FormData()
      fd.append('file', this.uploadFile)
      this.uploading = true
      this.uploadProgress = 0
      
      axios.post('/api/upload', fd, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (evt) => {
          if (evt.total) {
            this.uploadProgress = Math.round((evt.loaded / evt.total) * 100)
          }
        }
      }).then(res => {
        console.log('POST /api/upload ->', res.status, res.data)
        if (res.data?.status === 'success') {
          this.uploadSuccess = '上传成功'
          // 延迟后刷新文件列表
          setTimeout(() => {
            this.fetchFiles()
          }, 500)
          // 弹出结果确认框
          this.uploadResultMessage = '文件上传成功'
          this.uploadResultVisible = true
          // 重置选择
          this.uploadFile = null
          if (this.$refs.fileInput) this.$refs.fileInput.value = ''
        } else {
          this.uploadError = res.data?.message || '上传失败'
        }
      }).catch(err => {
        console.error('POST /api/upload error:', err)
        this.uploadError = err.response?.data?.message || err.message || '上传失败'
      }).finally(() => {
        this.uploading = false
        this.uploadProgress = 0
      })
    },
    fetchFiles() {
      this.filesLoading = true
      this.filesError = ''
      const guard = setTimeout(() => {
        if (this.filesLoading) {
          this.filesLoading = false
          this.filesError = '加载超时，请点击刷新重试'
        }
      }, 8000)
      axios.get('/api/uploads', { params: { page: this.page, page_size: this.page_size } })
        .then(res => {
          console.log('GET /api/uploads ->', res.status, res.data)
          clearTimeout(guard)
          if (res.data?.status === 'success') {
            const d = res.data.data || {}
            this.files = Array.isArray(d.items) ? d.items : (Array.isArray(d) ? d : [])
            this.total = d.total || 0
            this.filesError = ''
          } else {
            this.filesError = res.data?.message || '获取文件列表失败'
            this.files = []
          }
          this.filesLoading = false
        })
        .catch(err => {
          console.error('GET /api/uploads error:', err)
          clearTimeout(guard)
          this.filesError = err.response?.data?.message || err.message || '获取文件列表失败'
          this.files = []
          this.filesLoading = false
        })
    },
    changePage(p) { this.page = p; this.fetchFiles() },
    previewFile(f) {
      const token = localStorage.getItem('token') || ''
      const url = `/api/uploads/${f.id}/file?token=${encodeURIComponent(token)}`
      window.open(url, '_blank')
    },
    downloadFile(f) {
      const token = localStorage.getItem('token') || ''
      const url = `/api/uploads/${f.id}/download?token=${encodeURIComponent(token)}`
      const a = document.createElement('a')
      a.href = url
      a.download = f.original_name || 'download'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
    },
    removeFile(f) {
      if (!confirm(`确认删除文件: ${f.original_name} ?`)) return
      axios.delete(`/api/uploads/${f.id}`)
        .then(res => {
          if (res.data?.status === 'success') {
            this.fetchFiles()
          } else {
            alert(res.data?.message || '删除失败')
          }
        })
        .catch(err => { alert(err.response?.data?.message || err.message || '删除失败') })
    },

    // 上传结果确认
    confirmUploadResult() {
      this.uploadResultVisible = false
      this.uploadVisible = false
      this.uploadError = ''
      this.uploadSuccess = ''
      this.uploadProgress = 0
      // 确保文件列表已刷新
      if (this.files.length === 0 && this.activeMenu === 'files') {
        this.fetchFiles()
      }
    },

    // 通用
    formatDate(v) {
      if (!v) return '-'
      const t = Date.parse(v)
      if (isNaN(t)) return v
      return new Date(t).toLocaleString('zh-CN')
    },
    formatDateMs(ms) {
      if (ms == null) return '-'
      const d = new Date(Number(ms))
      if (isNaN(d.getTime())) return '-'
      return d.toLocaleString('zh-CN')
    },
    formatSize(b) {
      if (b == null) return '-'
      const units = ['B','KB','MB','GB','TB']
      let n = Number(b), i = 0
      while (n >= 1024 && i < units.length - 1) { n /= 1024; i++ }
      return `${n.toFixed(n < 10 && i > 0 ? 1 : 0)} ${units[i]}`
    },

    // 用户菜单
    openMenu() { this.menuOpen = true },
    closeMenu() { if (this._menuTimer) clearTimeout(this._menuTimer); this._menuTimer = setTimeout(() => { this.menuOpen = false }, 120) },
    toggleMenu() { if (this._menuTimer) clearTimeout(this._menuTimer); this.menuOpen = !this.menuOpen },
    onDocClick(e) { const el = this.$refs.userMenu; if (!el) return; if (!el.contains(e.target)) { this.menuOpen = false } },

    // 编辑弹窗
    openEdit() {
      try {
        const u = JSON.parse(localStorage.getItem('user') || 'null')
        if (u) { this.currentUser = u; this.editForm.id = u.id; this.editForm.username = u.username || ''; this.editForm.email = u.email || '' }
      } catch (e) {}
      this.editError = ''; this.editSuccess = ''
      this.editForm.old_password = ''; this.editForm.new_password = ''; this.editForm.confirm_password = ''
      this.editVisible = true
    },
    closeEdit() { this.editVisible = false },
    submitEdit() {
      this.editError = ''; this.editSuccess = ''
      if (this.editForm.username && this.editForm.username.length < 3) { this.editError = '用户名至少需要3个字符'; return }
      const changingPwd = !!this.editForm.new_password || !!this.editForm.confirm_password
      if (changingPwd) {
        if (!this.editForm.old_password) { this.editError = '请输入原密码'; return }
        if (!this.editForm.new_password || this.editForm.new_password.length < 6) { this.editError = '新密码至少需要6个字符'; return }
        if (this.editForm.new_password !== this.editForm.confirm_password) { this.editError = '两次输入的新密码不一致'; return }
      }
      this.editSubmitting = true
      axios.post('/api/users/update', {
        id: this.editForm.id,
        username: this.editForm.username,
        email: this.editForm.email,
        old_password: this.editForm.old_password || undefined,
        new_password: this.editForm.new_password || undefined
      }).then(res => {
        if (res.data && res.data.status === 'success') {
          const newUser = res.data.user
          this.currentUser = newUser
          try { localStorage.setItem('user', JSON.stringify(newUser)) } catch (e) {}
          this.editSuccess = '资料已更新'
          setTimeout(() => { this.editVisible = false }, 800)
        } else {
          this.editError = res.data?.message || '更新失败'
        }
      }).catch(err => {
        this.editError = err.response?.data?.message || err.message || '更新失败'
      }).finally(() => { this.editSubmitting = false })
    },

    // 登录态
    logout() {
      localStorage.removeItem('token'); localStorage.removeItem('user')
      alert('已退出登录')
      this.$router.push('/login')
    }
  },
  mounted() {
    try {
      const u = JSON.parse(localStorage.getItem('user') || 'null')
      if (u) { this.currentUser = u; this.editForm.id = u.id; this.editForm.username = u.username || ''; this.editForm.email = u.email || '' }
    } catch (e) {}
    document.addEventListener('click', this.onDocClick)
    // 进入首页时加载统计与轮播
    this.fetchStats()
    this.startCarousel()
    // 初始化时加载文件列表
    this.fetchFiles()
  },
  unmounted() {
    document.removeEventListener('click', this.onDocClick)
    this.stopCarousel()
  }
}
</script>

<style scoped>
.admin-layout { display: flex; height: 100vh; font-family: "Microsoft Yahei", Arial, sans-serif; }
.sidebar { width: 220px; background-color: #fff; color: #1f2d3d; display: flex; flex-direction: column; box-shadow: 2px 0 8px rgba(0,0,0,.06); }
.logo { height: 60px; font-size: 22px; font-weight: bold; display: flex; align-items: center; justify-content: center; line-height: 1; text-align: center; border-bottom: 1px solid #eef0f3; }
.sidebar nav ul { list-style: none; padding: 0; margin: 0; }
.sidebar nav ul li { padding: 15px 20px; cursor: pointer; user-select: none; transition: background-color 0.3s; display: flex; align-items: center; line-height: 1; }
.sidebar nav ul li:hover { background-color: #f5f7fa; }
.sidebar nav ul li.active { background-color: #e6f4ff; color: #1677ff; }
.main-content { flex: 1; display: flex; flex-direction: column; background: #f0f2f5; }
header { height: 60px; background: white; padding: 0 20px; display: flex; align-items: center; box-shadow: 0 2px 8px rgb(0 0 0 / 0.1); }
header h1 { margin: 0; font-size: 20px; font-weight: 600; line-height: 1; }

/* 右上角用户菜单 */
.header-right { margin-left: auto; }
.user-menu { position: relative; display: flex; align-items: center; gap: 6px; cursor: pointer; user-select: none; color: #333; }
.user-menu .user-name { font-weight: 600; }
.user-menu .caret { font-size: 12px; color: #999; }
.user-menu .dropdown { position: absolute; top: 100%; right: 0; background: #fff; border: 1px solid #eee; box-shadow: 0 6px 20px rgba(0,0,0,.12); border-radius: 8px; padding: 8px 0; min-width: 160px; z-index: 1000; }
.dropdown-item { padding: 10px 14px; font-size: 14px; color: #333; white-space: nowrap; }
.dropdown-item:hover { background: #f5f7fa; }
.dropdown-item.danger { color: #d93025; }

.content { padding: 20px; flex: 1; overflow-y: scroll; }

/* 首页样式 */
.home { padding: 20px; }
.home-hero { background: #fff; padding: 24px 28px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,.06); margin-bottom: 16px; }
.home-hero h2 { margin: 0 0 8px; color: #333; }
.home-hero p { margin: 0; color: #666; line-height: 1.7; }

/* 最新统计 */
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin: 12px 0 20px; }
.stat-card { background: #fff; padding: 16px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,.06); }
.stat-value { font-size: 22px; font-weight: 700; color: #1f2d3d; }
.stat-label { margin-top: 6px; color: #666; font-size: 13px; }

/* 轮播 */
.carousel { position: relative; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,.06); margin-bottom: 16px; }
.carousel-track { display: flex; width: 100%; transition: transform .5s ease; }
.carousel-slide { position: relative; min-width: 100%; height: 320px; display: flex; align-items: center; justify-content: center; background: #fff; }
.carousel-slide img { display: block; max-width: 100%; max-height: 100%; width: auto; height: auto; object-fit: contain; }
.carousel-caption { position: absolute; left: 0; right: 0; bottom: 0; padding: 10px 14px; color: #fff; background: linear-gradient(to top, rgba(0,0,0,.45), rgba(0,0,0,0)); font-size: 14px; }
.carousel .nav { position: absolute; top: 50%; transform: translateY(-50%); width: 36px; height: 36px; border: none; border-radius: 50%; background: rgba(0,0,0,.35); color: #fff; cursor: pointer; }
.carousel .nav:hover { background: rgba(0,0,0,.5); }
.carousel .prev { left: 10px; }
.carousel .next { right: 10px; }
.dots { position: absolute; left: 0; right: 0; bottom: 10px; display: flex; justify-content: center; gap: 8px; }
.dots span { width: 8px; height: 8px; border-radius: 50%; background: rgba(255,255,255,.6); cursor: pointer; }
.dots span.active { background: #fff; }

/* 三图拼接轮播布局 */
.multi-slide { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; height: 100%; align-items: center; padding: 0 10px; box-sizing: border-box; }
.tile { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: #fff; border-radius: 6px; overflow: hidden; }
.tile img { max-width: 100%; max-height: 100%; width: auto; height: auto; object-fit: contain; }

/* 危害卡片 */
.home-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin: 16px 0; }
.card { background: #fff; border-radius: 8px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,.06); }
.card h3 { margin: 0 0 8px; color: #333; }
.card p { margin: 0; color: #666; }

/* 典型影响 */
.home-section { background: #fff; padding: 16px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,.06); margin: 16px 0; }
.home-section h3 { margin: 0 0 8px; color: #333; }
.home-section ul { padding-left: 18px; margin: 0; color: #555; }
.home-section li { line-height: 1.8; }

/* 快捷入口 */
.entry-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin: 16px 0; }
.entry { background: #fff; border-radius: 8px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,.06); cursor: pointer; transition: transform .15s ease, box-shadow .15s ease; }
.entry:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(0,0,0,.08); }
.entry h4 { margin: 0 0 6px; color: #333; }
.entry p { margin: 0; color: #666; font-size: 13px; }

/* 文件管理 */
.files-page .uploader { display: flex; gap: 10px; align-items: center; }
.success { color: #2e7d32; text-align: left; padding: 8px 0; }
.progress { height: 8px; background: #f0f0f0; border-radius: 4px; overflow: hidden; margin: 6px 0 12px; }
.progress .bar { height: 100%; background: #1890ff; width: 0; transition: width .2s ease; }
.ops a { margin-right: 10px; color: #1890ff; text-decoration: none; cursor: pointer; }
.ops a:hover { text-decoration: underline; color: #40a9ff; }
.ops a:active { color: #096dd9; }
.pagination { display: flex; align-items: center; gap: 10px; justify-content: flex-end; margin-top: 12px; }
.pagination button { padding: 6px 12px; border: 1px solid #dcdfe6; background: #fff; border-radius: 4px; cursor: pointer; }
.pagination button:disabled { opacity: .6; cursor: not-allowed; }

/* 用户列表通用样式复用 */
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h3 { margin: 0; color: #333; }
.refresh-btn { padding: 8px 16px; background: #1890ff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
.refresh-btn:hover { background: #40a9ff; }
.loading, .error { text-align: left; padding: 8px 0; color: #666; }
.error { color: #d32f2f; }
.users-table { width: 100%; border-collapse: collapse; }
.users-table th, .users-table td { padding: 12px; text-align: left; border-bottom: 1px solid #f0f0f0; }
.users-table th { background: #fafafa; font-weight: 600; color: #333; }
.users-table tbody tr:hover { background: #fafafa; }
.empty { text-align: center; color: #999; padding: 40px; }

/* 编辑资料弹窗 */
.modal-mask { position: fixed; z-index: 4000; inset: 0; background: rgba(0,0,0,.35); display: flex; align-items: center; justify-content: center; padding: 20px; }
.modal-container { width: 420px; max-width: 90vw; background: #fff; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,.15); padding: 20px; }
.modal-title { margin: 0 0 12px; font-size: 18px; font-weight: 700; color: #333; }
.form-row { display: flex; flex-direction: column; gap: 6px; margin-bottom: 12px; }
.form-row label { font-size: 13px; color: #666; }
.form-row input { padding: 10px 12px; border: 1px solid #dcdfe6; border-radius: 6px; font-size: 14px; outline: none; }
.form-row input:focus { border-color: #1890ff; box-shadow: 0 0 0 2px rgba(24,144,255,.15); }
.divider { height: 1px; background: #f0f0f0; margin: 12px 0; }
.form-error { color: #d93025; margin: 6px 0; }
.form-success { color: #2e7d32; margin: 6px 0; }
.actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 8px; }
.actions button { padding: 8px 14px; border: 1px solid #dcdfe6; background: #fff; color: #333; border-radius: 6px; cursor: pointer; }
.actions button.primary { background: #1890ff; border-color: #1890ff; color: #fff; }
.actions button:disabled { opacity: .6; cursor: not-allowed; }

/* 文件管理-头部动作区 */
.file-actions { display: flex; align-items: center; gap: 10px; }

/* 上传弹窗细节 */
.upload-modal .hint { margin: 4px 0 12px; color: #666; font-size: 13px; }
.file-chooser { display: flex; align-items: center; gap: 10px; }
.file-chip { display: inline-flex; max-width: 260px; padding: 6px 10px; border-radius: 16px; background: #f5f7fa; color: #333; font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.file-chip.empty { color: #999; background: #fafafa; border: 1px dashed #e5e7eb; }
.choose-btn { display:inline-block; padding:8px 14px; background:#1890ff; color:#fff; border-radius:6px; cursor:pointer; user-select:none; border:none; font-size:14px; transition:background .2s ease; }
.choose-btn:hover { background:#40a9ff; }
.choose-btn:active { background:#096dd9; }

/* 文件管理-上传按钮（重新设计） */
.btn-upload { 
  display: inline-flex; align-items: center; gap: 8px;
  padding: 10px 16px; border-radius: 8px; 
  border: 1px solid #1677ff; color: #fff; 
  background: linear-gradient(90deg, #1677ff 0%, #4096ff 100%);
  box-shadow: 0 4px 10px rgba(22, 119, 255, 0.25);
  cursor: pointer; font-weight: 600; font-size: 14px;
  transition: background .2s ease, box-shadow .2s ease, transform .08s ease;
}
.btn-upload:hover { 
  background: linear-gradient(90deg, #3b8cff 0%, #62a6ff 100%);
  box-shadow: 0 6px 14px rgba(22, 119, 255, 0.32);
}
.btn-upload:active { 
  transform: translateY(1px);
}
.btn-upload:focus-visible { 
  outline: none; box-shadow: 0 0 0 3px rgba(22,119,255,.2);
}
.btn-upload .icon { 
  width: 16px; height: 16px; flex: 0 0 16px;
}
.btn-upload[disabled] { opacity: .6; cursor: not-allowed; box-shadow: none; }

/* 典型影响优化样式 */
.impact-section { background:#fff; padding:16px; border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,.06); margin:16px 0; }
.impact-section h3 { margin:0 0 12px; color:#333; }
.impact-grid { display:grid; grid-template-columns: repeat(3, 1fr); gap:16px; }
.impact-card { position:relative; background:#fff; border:1px solid #f0f0f0; border-radius:10px; padding:14px 16px; transition: transform .15s ease, box-shadow .15s ease; }
.impact-card:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(0,0,0,.08); }
.impact-badge { width:36px; height:4px; border-radius:2px; background: linear-gradient(90deg, #1890ff, #73d13d); margin-bottom:10px; }
.impact-title { margin:0 0 6px; font-size:16px; color:#1f2d3d; font-weight:700; }
.impact-desc { margin:0; color:#666; line-height:1.7; font-size:14px; }

@media (max-width: 768px) {
  .impact-grid { grid-template-columns: 1fr; }
}
</style>
