<template>
  <div class="admin-layout">
    <aside
      :class="['sidebar', { hidden: sidebarHidden, peek: sidebarHidden && sidebarPeek }]"
      @mouseenter="onSidebarMouseEnter"
      @mouseleave="onSidebarMouseLeave"
    >
      <!-- 折叠按钮（位于边栏内） -->
      <button class="sidebar-toggle" @click="toggleSidebar" title="隐藏边栏" aria-label="隐藏边栏">«</button>
      <router-link class="logo" to="/dashboard" title="返回首页">
        <img class="logo-mark" src="/brand/logo.svg" alt="Logo" />
        <span class="logo-text">谣言关键传播者<br>识别系统</span>
      </router-link>
      <Sidebar />
    </aside>

    <!-- 左侧边缘感应区（隐藏状态下，鼠标移入可临时展开） -->
    <div
      v-if="sidebarHidden && !sidebarPeek"
      class="left-edge-sensor"
      @mouseenter="openPeek"
      aria-hidden="true"
    ></div>

    <!-- 展开按钮（边栏隐藏时显示，悬浮在左上角） -->
    <button v-if="sidebarHidden && !sidebarPeek" class="sidebar-show-btn" @click="toggleSidebar" title="展开边栏" aria-label="展开边栏">»</button>

    <div class="main-content">
      <HeaderBar :title="pageTitle" />
      <section class="content">
        <router-view />
      </section>
    </div>
  </div>
</template>

<script>
import Sidebar from '../components/Sidebar.vue'
import HeaderBar from '../components/HeaderBar.vue'

export default {
  name: 'AdminLayout',
  components: { Sidebar, HeaderBar },
  data() {
    return { sidebarHidden: false, sidebarPeek: false, _peekTimer: null }
  },
  computed: {
    pageTitle() {
      const p = this.$route.path
      if (p.startsWith('/dashboard')) return '首页'
      if (p.startsWith('/users')) return '用户管理'
      if (p.startsWith('/algorithms')) return '算法管理'
      if (p.startsWith('/files')) return '文件管理'
      if (p.startsWith('/settings')) return '系统设置'
      return ''
    }
  },
  methods: {
    toggleSidebar() {
      this.sidebarHidden = !this.sidebarHidden
      if (this.sidebarHidden) this.sidebarPeek = false
    },
    openPeek() {
      if (!this.sidebarHidden) return
      if (this._peekTimer) clearTimeout(this._peekTimer)
      this.sidebarPeek = true
    },
    onSidebarMouseEnter() {
      if (this._peekTimer) clearTimeout(this._peekTimer)
    },
    onSidebarMouseLeave() {
      if (!this.sidebarHidden) return
      if (this._peekTimer) clearTimeout(this._peekTimer)
      this._peekTimer = setTimeout(() => { this.sidebarPeek = false }, 160)
    }
  }
}
</script>

<style scoped>
.admin-layout { display: flex; height: 100vh; font-family: "Microsoft Yahei", Arial, sans-serif; position: relative; }
.sidebar { width: 220px; background-color: #fff; color: #1f2d3d; display: flex; flex-direction: column; box-shadow: 2px 0 8px rgba(0,0,0,.06); position: relative; overflow: hidden; transition: width 0.25s ease; }
.sidebar.hidden { width: 0; box-shadow: none; pointer-events: none; }
/* 悬浮预览状态：以覆盖层形式显示，可点击 */
.sidebar.peek { position: absolute; left: 0; top: 0; height: 100%; width: 220px; box-shadow: 2px 0 12px rgba(0,0,0,.12); z-index: 20; pointer-events: auto; }

.main-content { flex: 1; display: flex; flex-direction: column; background: #f0f2f5; }
.content { padding: 20px; flex: 1; overflow-y: auto; }

/* 顶部 Logo 区域 */
.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 0 8px;
  text-align: center;
  line-height: 1.1;
  border-bottom: none;
  user-select: none;
  cursor: pointer;
  text-decoration: none;
}
.logo-mark {
  width: 22px; height: 22px; object-fit: contain;
  filter: drop-shadow(0 0 6px rgba(99,102,241,.35));
}
.logo-text {
  /* 字体与权重 */
  font-family: 'Orbitron', 'Microsoft Yahei', Arial, sans-serif;
  font-size: 20px; font-weight: 800; letter-spacing: 0.5px;
  /* 使用登录欢迎页相同的深灰色 */
  color: #4a5568;
}
.logo:hover .logo-text {
  transform: translateY(-1px) scale(1.02);
  text-shadow: 0 0 12px rgba(99, 102, 241, 0.5), 0 0 24px rgba(244, 114, 182, 0.45);
}
@keyframes gradientShift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
@keyframes glowPulse {
  0% { text-shadow: 0 0 6px rgba(99,102,241,.25), 0 0 12px rgba(34,211,238,.25); }
  50% { text-shadow: 0 0 12px rgba(99,102,241,.55), 0 0 28px rgba(244,114,182,.45); }
  100% { text-shadow: 0 0 6px rgba(99,102,241,.25), 0 0 12px rgba(34,211,238,.25); }
}
@media (prefers-reduced-motion: reduce) {
  .logo-text { animation: none; }
}
@media (max-width: 420px) {
  .logo-text { font-size: 18px; }
}

/* 边栏内的折叠按钮（下移以避免与标题重叠） */
.sidebar-toggle {
  position: absolute;
  top: calc(64px + 8px); right: 8px; /* 放在 logo 区域(64px)下方 8px */
  width: 28px; height: 28px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #fff;
  color: #4b5563;
  cursor: pointer;
  display: inline-flex; align-items: center; justify-content: center;
  box-shadow: 0 2px 6px rgba(0,0,0,.06);
}
.sidebar-toggle:hover { background: #f9fafb; }

/* 隐藏时显示的展开按钮（悬浮） */
.sidebar-show-btn {
  position: absolute;
  top: calc(60px + 10px); left: 8px; /* 避开头部标题（HeaderBar 高度 60px），下移 10px */
  z-index: 10;
  width: 30px; height: 30px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #fff;
  color: #4b5563;
  cursor: pointer;
  display: inline-flex; align-items: center; justify-content: center;
  box-shadow: 0 2px 10px rgba(0,0,0,.12);
}
.sidebar-show-btn:hover { background: #f9fafb; }

/* 左侧边缘感应区 */
.left-edge-sensor {
  position: fixed;
  left: 0; top: 0;
  width: 8px; height: 100vh;
  z-index: 15;
  background: transparent; /* 不可见但可捕获鼠标 */
}
</style>
