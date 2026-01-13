<template>
  <div class="dashboard">
    <!-- 欢迎区 -->
    <div class="welcome-section">
      <div class="welcome-head">
        <h2 class="welcome-title">欢迎进入谣言关键传播者检测平台</h2>
        <p class="welcome-sub">在这里，你可以高效识别潜在的关键传播者，分析传播路径，降低谣言风险。</p>
      </div>
    </div>
    <!-- 今日辟谣 + 联合辟谣（并排） -->
    <div class="debunks-row">
      <!-- 今日辟谣 -->
      <div class="debunk-section">
        <div class="debunk-header">
          <h3>{{ debunksHeaderText || '今日辟谣' }}</h3>
          <div class="debunk-actions">
            <button class="debunk-refresh" @click="fetchDebunks" :disabled="debunksLoading">{{ debunksLoading ? '刷新中...' : '刷新' }}</button>
          </div>
        </div>
        <div v-if="debunksError" class="debunk-error">{{ debunksError }}</div>
        <div v-else-if="debunksLoading" class="debunk-loading">加载中...</div>
        <ul v-else class="debunk-list">
          <li v-for="item in debunks" :key="item.id || item.link" class="debunk-item">
            <a class="debunk-title" :href="item.link" target="_blank" rel="noopener noreferrer">{{ item.title }}</a>
          </li>
          <li v-if="debunks.length === 0" class="debunk-empty">暂无辟谣信息</li>
        </ul>
        <div class="debunk-note">数据来源于中国互联网联合辟谣平台，点击标题前往原文查看详情。</div>
      </div>

      <!-- 联合辟谣 -->
      <div class="debunk-section">
        <div class="debunk-header">
          <h3>{{ unionHeader || '联合辟谣' }}</h3>
          <div class="debunk-actions">
            <button class="debunk-refresh" @click="fetchUnionDebunks" :disabled="unionDebunksLoading">{{ unionDebunksLoading ? '刷新中...' : '刷新' }}</button>
          </div>
        </div>
        <div v-if="unionDebunksError" class="debunk-error">{{ unionDebunksError }}</div>
        <div v-else-if="unionDebunksLoading" class="debunk-loading">加载中...</div>
        <ul v-else class="debunk-list">
          <li v-for="item in unionDebunks" :key="item.id || item.link" class="debunk-item">
            <a class="debunk-title" :href="item.link" target="_blank" rel="noopener noreferrer">{{ item.title }}</a>
          </li>
          <li v-if="unionDebunks.length === 0" class="debunk-empty">暂无联合辟谣信息</li>
        </ul>
        <div class="debunk-note">数据来源于中国互联网联合辟谣平台，点击标题前往原文查看详情。</div>
      </div>
    </div>


    <!-- 危害模块（与 Home.vue 保持一致） -->
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


    <!-- 轮播图（每屏三图拼接） -->
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

   

    

    <!-- 典型影响（卡片网格，3列x2行） -->
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

    

    <!-- 底部统计 -->
    <div class="stats stats-bottom" ref="statsSection">
      <div class="stat-card">
        <div class="stat-value">{{ statsLoading ? '...' : (isAdmin ? (stats?.users_total ?? 0) : (stats?.uploads_total ?? 0)) }}</div>
        <div class="stat-label">{{ isAdmin ? '用户总数' : '我的上传文件数' }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ statsLoading ? '...' : (isAdmin ? formatDate(stats?.latest_user_created_at) : (stats?.tasks_total ?? 0)) }}</div>
        <div class="stat-label">{{ isAdmin ? '最近注册时间' : '我的识别任务总数' }}</div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
export default {
  name: 'Dashboard',
  data() {
    return {
      isAdmin: false,
      // 今日辟谣
      debunks: [],
      debunksLoading: false,
      debunksError: '',
      debunksTimer: null,
      debunksHeaderText: '',
      // 联合辟谣
      unionHeader: '',
      unionDebunks: [],
      unionDebunksLoading: false,
      unionDebunksError: '',
      unionDebunksTimer: null,
      // 统计
      stats: null,
      statsLoading: false,
      statsError: '',
      // 轮播
      carouselIndex: 0,
      carouselTimer: null,
      carouselImages: [
        { src: '/images/rumor1.JPG', alt: '谣言治理图1', caption: '关键传播者识别' },
        { src: '/images/rumor2.jpg', alt: '谣言治理图2', caption: '传播路径可视化' },
        { src: '/images/rumor3.jpeg', alt: '谣言治理图3', caption: '风险预警与干预' },
        { src: '/images/rumor4.webp', alt: '谣言治理图4', caption: '多源数据融合' },
        { src: '/images/rumor5.png', alt: '谣言治理图5', caption: '全流程治理闭环' },
        { src: '/images/rumor6.png', alt: '谣言治理图6', caption: '多方协同治理' }
      ],
      impacts: [
        { title: '社会情绪与行为', desc: '公共事件期间引发情绪失控与囤积行为，扰乱供应链并造成价格波动。' },
        { title: '健康与安全误导', desc: '医疗与安全谣言使公众延误正确处置与求助，扩大事件影响范围。' },
        { title: '机构与企业声誉', desc: '谣言冲击组织信任与品牌形象，带来长期声誉风险与经济损失。' },
        { title: '政策与治理成本', desc: '干扰公共决策，导致资源错配，提升辟谣澄清的治理成本。' },
        { title: '个人权益与隐私', desc: '隐私泄露与网络暴力增多，个人名誉与心理健康受到伤害。' },
        { title: '平台生态与合规', desc: '平台生态恶化、合规压力上升，需强化风控与内容治理能力。' }
      ]
    }
  },
  computed: {
    carouselSlides() {
      const size = 3
      const arr = this.carouselImages || []
      const groups = []
      for (let i = 0; i < arr.length; i += size) groups.push(arr.slice(i, i + size))
      return groups
    },
    debunksHeader() {
      const d = this.debunksHeaderDate
      if (!d) return ''
      const y = d.getFullYear()
      const m = d.getMonth() + 1
      const day = d.getDate()
      return `今日辟谣（${y}年${m}月${day}日）`
    },
    debunksHeaderDate() {
      const arr = this.debunks || []
      if (!arr.length) return null
      // 1) 优先用第一条的 published_at
      const v = arr[0] && (arr[0].published_at || arr[0].date)
      let d = this.parseDateSafe(v)
      if (d) return d
      // 2) 退化：从链接里的日期片段提取（例如 .../20251205/...）
      const link = arr[0] && arr[0].link
      if (link) {
        const m = String(link).match(/\/(\d{8})\//)
        if (m) {
          const y = m[1].slice(0,4), mo = m[1].slice(4,6), da = m[1].slice(6,8)
          d = this.parseDateSafe(`${y}-${mo}-${da} 08:00:00`)
          if (d) return d
        }
      }
      return null
    }
  },
  methods: {
    checkUserRole() {
      try {
        const raw = localStorage.getItem('user')
        const u = raw ? JSON.parse(raw) : null
        this.isAdmin = u && u.role === 'admin'
      } catch (e) {
        this.isAdmin = false
      }
    }, 
    fetchDebunks() {
      this.debunksLoading = true
      this.debunksError = ''
      axios.get('/api/debunks/live', { params: { limit: 10 } })
        .then(res => {
          if (res.data?.status === 'success') {
            const arr = Array.isArray(res.data.data) ? res.data.data : []
            if (arr.length > 0) {
              this.debunksHeaderText = (typeof arr[0] === 'string') ? arr[0] : (arr[0]?.title || '')
              this.debunks = arr.slice(1)
            } else {
              this.debunksHeaderText = ''
              this.debunks = []
            }
          } else if (Array.isArray(res.data)) {
            const arr = res.data
            this.debunksHeaderText = (typeof arr[0] === 'string') ? arr[0] : (arr[0]?.title || '')
            this.debunks = arr.slice(1)
          } else {
            this.debunksError = res.data?.message || '获取辟谣信息失败'
            this.debunksHeaderText = ''
            this.debunks = []
          }
        })
        .catch(err => {
          this.debunksError = err.response?.data?.message || err.message || '获取辟谣信息失败'
          this.debunks = []
        })
        .finally(() => { this.debunksLoading = false })
    },
    fetchUnionDebunks() {
      this.unionDebunksLoading = true
      this.unionDebunksError = ''
      axios.get('/api/debunks/lianhe', { params: { limit: 10 } })
        .then(res => {
          if (res.data?.status === 'success') {
            const arr = Array.isArray(res.data.data) ? res.data.data : []
            if (arr.length > 0) {
              this.unionHeader = arr[0]|| ''
              this.unionDebunks = arr.slice(1)
            } else {
              this.unionHeader = ''
              this.unionDebunks = []
            }
          } else if (Array.isArray(res.data)) {
            const arr = res.data
            this.unionHeader = arr[0]?.title || ''
            this.unionDebunks = arr.slice(1)
          } else {
            this.unionDebunksError = res.data?.message || '获取联合辟谣信息失败'
            this.unionHeader = ''
            this.unionDebunks = []
          }
        })
        .catch(err => {
          this.unionDebunksError = err.response?.data?.message || err.message || '获取联合辟谣信息失败'
          this.unionHeader = ''
          this.unionDebunks = []
        })
        .finally(() => { this.unionDebunksLoading = false })
    },
    startDebunksPolling() {
      this.stopDebunksPolling()
      // 每5分钟自动刷新一次
      this.debunksTimer = setInterval(() => { this.fetchDebunks() }, 5 * 60 * 1000)
    },
    stopDebunksPolling() { if (this.debunksTimer) { clearInterval(this.debunksTimer); this.debunksTimer = null } },
    startUnionDebunksPolling() {
      this.stopUnionDebunksPolling()
      this.unionDebunksTimer = setInterval(() => { this.fetchUnionDebunks() }, 5 * 60 * 1000)
    },
    stopUnionDebunksPolling() { if (this.unionDebunksTimer) { clearInterval(this.unionDebunksTimer); this.unionDebunksTimer = null } },
    fetchStats() {
      this.statsLoading = true
      this.statsError = ''
      const endpoint = this.isAdmin ? '/api/stats' : '/api/stats/me'
      axios.get(endpoint)
        .then(res => {
          if (res.data?.status === 'success') this.stats = res.data.data || null
          else this.statsError = res.data?.message || '获取统计失败'
        })
        .catch(err => { this.statsError = err.response?.data?.message || err.message || '获取统计失败' })
        .finally(() => { this.statsLoading = false })
    },
    startCarousel() { this.stopCarousel(); this.carouselTimer = setInterval(() => { this.nextSlide() }, 5000) },
    stopCarousel() { if (this.carouselTimer) { clearInterval(this.carouselTimer); this.carouselTimer = null } },
    nextSlide() { const n = this.carouselSlides.length; if (!n) return; this.carouselIndex = (this.carouselIndex + 1) % n },
    prevSlide() { const n = this.carouselSlides.length; if (!n) return; this.carouselIndex = (this.carouselIndex - 1 + n) % n },
    goSlide(i) { if (i >= 0 && i < this.carouselSlides.length) this.carouselIndex = i },
    formatDate(v) {
      if (!v) return '-'
      const d = this.parseDateSafe(v)
      if (!d) return typeof v === 'string' ? v : '-'
      try { return d.toLocaleString('zh-CN') } catch (e) { return typeof v === 'string' ? v : '-' }
    },
    formatDateCN(v) {
      const d = this.parseDateSafe(v)
      if (!d) return ''
      const y = d.getFullYear()
      const m = d.getMonth() + 1
      const day = d.getDate()
      return `${y}年${m}月${day}日`
    },
    parseDateSafe(v) {
      if (!v) return null
      const s = String(v).trim()
      let d = new Date(s)
      if (!isNaN(d.getTime())) return d
      // 尝试添加 T 分隔符
      let s2 = s.replace(' ', 'T')
      d = new Date(s2)
      if (!isNaN(d.getTime())) return d
      // Safari 兼容：用斜杠
      s2 = s.replace(/-/g, '/')
      d = new Date(s2)
      if (!isNaN(d.getTime())) return d
      // 正则兜底
      const m = s.match(/(\d{4})-(\d{1,2})-(\d{1,2})/)
      if (m) {
        const y = Number(m[1])
        const mo = Number(m[2]) - 1
        const da = Number(m[3])
        const tm = (s.match(/(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?/) || [])
        const hh = Number(tm[1] || 0)
        const mm = Number(tm[2] || 0)
        const ss = Number(tm[3] || 0)
        d = new Date(y, mo, da, hh, mm, ss)
        if (!isNaN(d.getTime())) return d
      }
      return null
    },
    scrollToStats() {
      this.$nextTick(() => {
        const el = this.$refs.statsSection
        if (el && el.scrollIntoView) {
          try { el.scrollIntoView({ behavior: 'smooth', block: 'start' }) } catch (e) { el.scrollIntoView() }
          return
        }
        // 兜底：手动计算容器滚动
        const container = document.querySelector('.content')
        if (container && el) {
          const cRect = container.getBoundingClientRect()
          const eRect = el.getBoundingClientRect()
          const top = eRect.top - cRect.top + container.scrollTop - 8 // 轻微上边距
          container.scrollTo({ top, behavior: 'smooth' })
        }
      })
    }
  },
  mounted() { this.checkUserRole(); this.fetchStats(); this.startCarousel(); this.fetchDebunks(); this.startDebunksPolling(); this.fetchUnionDebunks(); this.startUnionDebunksPolling() },
  unmounted() { this.stopCarousel(); this.stopDebunksPolling(); this.stopUnionDebunksPolling() }
}
</script>

<style scoped>
.dashboard { display: block; }
/* 危害模块样式 */
.home-hero { background: #fff; padding: 24px 28px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,.06); margin-bottom: 16px; }
.hero-grid { display: grid; grid-template-columns: 1.4fr 1fr; gap: 16px; align-items: center; }
.hero-text h2 { margin: 0 0 10px; color: #1f2d3d; }
.hero-intro { margin: 0; color: #555; line-height: 1.8; }
.hero-bullets { list-style: none; padding: 0; margin: 12px 0 10px; display: grid; gap: 8px; }
.hero-bullets li { display: flex; align-items: flex-start; gap: 8px; color: #555; }
.hero-bullets .dot { width: 8px; height: 8px; border-radius: 50%; background: #1890ff; margin-top: 6px; flex: 0 0 8px; }
.hero-tags { display: flex; flex-wrap: wrap; gap: 8px; margin: 8px 0 0; }
.hero-tags .tag { background: #f5f7fa; color: #333; border-radius: 14px; padding: 6px 10px; font-size: 12px; border: 1px solid #e5e7eb; }
.hero-media .media-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.hero-media .media-grid img { width: 100%; height: 120px; object-fit: cover; border-radius: 8px; background: #f5f5f5; }
.hero-media .media-grid img:nth-child(1) { grid-column: 1 / -1; height: 180px; }

/* 轮播 */
.carousel { position: relative; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,.06); margin-bottom: 16px; }
.carousel-track { display: flex; width: 100%; transition: transform .5s ease; }
.carousel-slide { position: relative; min-width: 100%; height: 320px; display: flex; align-items: center; justify-content: center; background: #fff; }
.multi-slide { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; height: 100%; align-items: center; padding: 0 10px; box-sizing: border-box; }
.tile { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: #fff; border-radius: 6px; overflow: hidden; }
.tile img { max-width: 100%; max-height: 100%; width: auto; height: auto; object-fit: contain; }
.carousel .nav { position: absolute; top: 50%; transform: translateY(-50%); width: 36px; height: 36px; border: none; border-radius: 50%; background: rgba(0,0,0,.35); color: #fff; cursor: pointer; }
.carousel .nav:hover { background: rgba(0,0,0,.5); }
.carousel .prev { left: 10px; }
.carousel .next { right: 10px; }
.dots { position: absolute; left: 0; right: 0; bottom: 10px; display: flex; justify-content: center; gap: 8px; }
.dots span { width: 8px; height: 8px; border-radius: 50%; background: rgba(255,255,255,.6); cursor: pointer; }
.dots span.active { background: #fff; }

/* 简要卡片 */
.home-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin: 16px 0; }
.card { background: #fff; border-radius: 8px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,.06); }
.card h3 { margin: 0 0 8px; color: #333; }
.card p { margin: 0; color: #666; }

/* 典型影响 */
.impact-section { background:#fff; padding:16px; border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,.06); margin:16px 0; }
.impact-section h3 { margin:0 0 12px; color:#333; }
.impact-grid { display:grid; grid-template-columns: repeat(3, 1fr); gap:16px; }
.impact-card { position:relative; background:#fff; border:1px solid #f0f0f0; border-radius:10px; padding:14px 16px; transition: transform .15s ease, box-shadow .15s ease; }
.impact-card:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(0,0,0,.08); }
.impact-badge { width:36px; height:4px; border-radius:2px; background: linear-gradient(90deg, #1890ff, #73d13d); margin-bottom:10px; }
.impact-title { margin:0 0 6px; font-size:16px; color:#1f2d3d; font-weight:700; }
.impact-desc { margin:0; color:#666; line-height:1.7; font-size:14px; }

/* 快捷入口 */
.entry-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin: 16px 0; }
.entry { background: #fff; border-radius: 8px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,.06); cursor: pointer; transition: transform .15s ease, box-shadow .15s ease; }
.entry:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(0,0,0,.08); }
.entry h4 { margin: 0 0 6px; color: #333; }
.entry p { margin: 0; color: #666; font-size: 13px; }

/* 底部统计 */
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin: 12px 0 20px; }
.stat-card { background: #fff; padding: 16px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,.06); }
.stat-value { font-size: 22px; font-weight: 700; color: #1f2d3d; }
.stat-label { margin-top: 6px; color: #666; font-size: 13px; }

@media (max-width: 1024px) { .hero-grid { grid-template-columns: 1fr; } }
@media (max-width: 768px) { .impact-grid { grid-template-columns: 1fr; } }
/* 欢迎区 */
.welcome-section { background:#fff; padding:16px 20px; border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,.06); margin-bottom:16px; }
.welcome-head { margin-bottom: 12px; }
.welcome-title { margin:0 0 6px; font-size:22px; font-weight:800; color:#1f2d3d; }
.welcome-sub { margin:0; color:#666; }
.welcome-grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap:12px; margin-top:12px; }
.welcome-item { background:#fff; border:1px solid #f0f0f0; border-radius:8px; padding:12px 14px; box-shadow: 0 1px 3px rgba(0,0,0,.02); }
.welcome-item h4 { margin:0 0 6px; font-size:16px; color:#1f2d3d; }
.welcome-item p { margin:0 0 10px; color:#666; line-height:1.7; font-size:14px; }
.welcome-btn { padding:8px 12px; border:none; border-radius:6px; background:#1677ff; color:#fff; cursor:pointer; font-size:14px; transition:background .2s ease, transform .08s ease; }
.welcome-btn:hover { background:#4096ff; }
.welcome-btn:active { transform: translateY(1px); }
.welcome-note { margin-top:10px; color:#888; font-size:12px; }

@media (max-width: 480px) { .welcome-title { font-size:20px; } }

/* 今日辟谣（与其他卡片样式一致） */
.debunks-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
@media (max-width: 900px) { .debunks-row { grid-template-columns: 1fr; } }
.debunk-section { background:#fff; padding:16px; border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,.06); }
.debunk-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; }
.debunk-header h3 { margin:0; color:#333; }
.debunk-actions { display:flex; align-items:center; gap:8px; }
.debunk-refresh { padding:6px 12px; border:1px solid #dcdfe6; background:#fff; border-radius:6px; cursor:pointer; }
.debunk-refresh:hover { background:#f5f7fa; }
.debunk-loading, .debunk-error { color:#666; padding:6px 0; }
.debunk-error { color:#d93025; }
.debunk-list { list-style:none; margin:0; padding:0; }
.debunk-item { padding:10px 0; border-bottom:1px solid #f0f0f0; }
.debunk-item:last-child { border-bottom:none; }
.debunk-title { color:#1677ff; text-decoration:none; }
.debunk-title:hover { text-decoration:underline; }
.debunk-meta { color:#999; font-size:12px; margin-top:4px; display:flex; align-items:center; gap:6px; }
.debunk-empty { color:#999; text-align:center; padding:16px 0; }
.debunk-note { color:#888; font-size:12px; margin-top:8px; }

</style>
