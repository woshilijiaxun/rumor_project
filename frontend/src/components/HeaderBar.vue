<template>
  <header class="header-bar">
    <h1 class="title">{{ title }}</h1>
    <div class="spacer"></div>
    <div class="user-menu" @mouseenter="openMenu" @mouseleave="closeMenu" @click="toggleMenu" ref="userMenu">
      <span class="user-name">{{ currentUser ? currentUser.username : '未登录' }}</span>
      <span class="caret">▾</span>
      <div class="dropdown" v-show="menuOpen" @click.stop>
        <div class="dropdown-item" @click="$emit('edit-profile')">修改账号/密码</div>
        <div class="dropdown-item danger" @click="logout">退出登录</div>
      </div>
    </div>
  </header>
</template>

<script>
export default {
  name: 'HeaderBar',
  props: { title: { type: String, default: '' } },
  data() {
    return { currentUser: null, menuOpen: false, _menuTimer: null }
  },
  mounted() {
    try { this.currentUser = JSON.parse(localStorage.getItem('user') || 'null') } catch (e) {}
    document.addEventListener('click', this.onDocClick)
  },
  unmounted() { document.removeEventListener('click', this.onDocClick) },
  methods: {
    openMenu() { this.menuOpen = true },
    closeMenu() { if (this._menuTimer) clearTimeout(this._menuTimer); this._menuTimer = setTimeout(() => { this.menuOpen = false }, 120) },
    toggleMenu() { if (this._menuTimer) clearTimeout(this._menuTimer); this.menuOpen = !this.menuOpen },
    onDocClick(e) { const el = this.$refs.userMenu; if (!el) return; if (!el.contains(e.target)) { this.menuOpen = false } },
    logout() {
      localStorage.removeItem('token'); localStorage.removeItem('user')
      alert('已退出登录')
      this.$router.push('/login')
    }
  }
}
</script>

<style scoped>
.header-bar { height: 60px; background: white; padding: 0 20px; display: flex; align-items: center; box-shadow: 0 2px 8px rgb(0 0 0 / 0.1); }
.title { margin: 0; font-size: 20px; font-weight: 600; line-height: 1; }
.spacer { flex: 1; }
.user-menu { position: relative; display: flex; align-items: center; gap: 6px; cursor: pointer; user-select: none; color: #333; }
.user-menu .user-name { font-weight: 600; }
.user-menu .caret { font-size: 12px; color: #999; }
.user-menu .dropdown { position: absolute; top: 100%; right: 0; background: #fff; border: 1px solid #eee; box-shadow: 0 6px 20px rgba(0,0,0,.12); border-radius: 8px; padding: 8px 0; min-width: 160px; z-index: 1000; }
.dropdown-item { padding: 10px 14px; font-size: 14px; color: #333; white-space: nowrap; }
.dropdown-item:hover { background: #f5f7fa; }
.dropdown-item.danger { color: #d93025; }
</style>

