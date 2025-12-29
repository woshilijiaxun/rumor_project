<template>
  <AuthLayout noDark :showContainer="showLogin">
    <template #header>
      <div v-if="!showLogin" class="welcome-overlay" @click="enter">
        <div class="welcome-lines">
          <div class="line l1">欢迎来到</div>
          <div class="line l2">谣言关键传播者</div>
          <div class="line l3">识别系统</div>
          <div class="enter-hint">
            <span class="enter-text">ENTER</span>
          </div>
        </div>
      </div>
    </template>
    <transition name="fade-up">
      <div v-if="showLogin">
        <h2>用户登录</h2>
        <div class="form-group">
          <input v-model="username" placeholder="用户名" class="form-input" />
        </div>
        <div class="form-group">
          <input v-model="password" type="password" placeholder="密码" class="form-input" />
        </div>
        <button @click="handleLogin" class="auth-btn">登录</button>
        <p v-if="message" :class="{'success-msg': isSuccess, 'error-msg': !isSuccess}">{{ message }}</p>
        <p class="link-text">
          还没有账号？<a @click="goToRegister">立即注册</a>
        </p>
      </div>
    </transition>
  </AuthLayout>
</template>

<script>
import axios from 'axios'
import AuthLayout from '../layouts/AuthLayout.vue'

export default {
  components: { AuthLayout },
  data() {
    return {
      username: '',
      password: '',
      message: '',
      isSuccess: false,
      showLogin: false
    }
  },
  mounted() {
    window.addEventListener('keydown', this.onKeyDown)
  },
  beforeUnmount() {
    window.removeEventListener('keydown', this.onKeyDown)
  },
  methods: {
    onKeyDown(e) {
      if (e.key === 'Enter') {
        if (!this.showLogin) {
          e.preventDefault()
          this.enter()
        } else if (this.username && this.password) {
          e.preventDefault()
          this.handleLogin()
        }
      }
    },
    enter() {
      this.showLogin = true
    },
    handleLogin() {
      axios.post('/api/login', {
        username: this.username,
        password: this.password
      })
      .then(response => {
        this.message = response.data.message
        this.isSuccess = response.data.status === 'success'
        if (this.isSuccess) {
          const token = response.data.token || ''
          if (token) {
            localStorage.setItem('token', token)
            try { this.$nextTick(() => { /* 确保本页后续请求也带上token */ }); } catch(e) {}
            try { axios.defaults.headers.common = axios.defaults.headers.common || {}; axios.defaults.headers.common.Authorization = `Bearer ${token}` } catch(e) {}
          }
          if (response.data.user) {
            try { localStorage.setItem('user', JSON.stringify(response.data.user)) } catch(e) {}
          }
          const raw = this.$route.query.redirect
          let target = raw ? decodeURIComponent(raw) : '/dashboard'
          if (typeof target === 'string' && !target.startsWith('/')) target = '/' + target
          this.$nextTick(() => {
            this.$router.replace(target).catch(() => {})
          })
        }
      })
      .catch(error => {
        this.isSuccess = false
        if (error.response && error.response.data) {
          this.message = error.response.data.message || '登录失败'
        } else {
          this.message = '登录失败: ' + error.message
        }
      })
    },
    goToRegister() {
      this.$router.push('/register')
    }
  }
}
</script>

<style scoped>
/***** 欢迎覆盖层样式 *****/
.auth-header { height: 100%; }
.welcome-overlay {
  position: relative;
  height: 100%;
  width: 100%; /* 让整个右侧区域都可点击 */
  display: flex;
  flex-direction: column;
  justify-content: center; /* 让三行字居于垂直中部 */
  align-items: flex-end; /* 内容贴近右侧，与登录卡片对齐 */
  padding: clamp(24px, 3vw, 40px);
  cursor: pointer;
  user-select: none;
  transform: translateY(-8vh);
}
.welcome-lines { width: fit-content; max-width: 90vw; display: flex; flex-direction: column; align-items: center; text-align: center; margin-left: auto; margin-right: clamp(16px, 3vw, 48px); }
.welcome-lines .line {
  color: #4a5568; /* 深灰色 */
  text-shadow: 0 2px 10px rgba(255, 255, 255, 0.4);
  font-weight: 800;
  letter-spacing: 1px;
  opacity: 0;
  transform: translateX(20px);
  animation: lineIn 600ms ease forwards;
}
.welcome-lines .l1 { font-size: clamp(40px, 3vw, 96px); animation-delay: 0ms; }
.welcome-lines .l2 { font-size: clamp(40px, 5vw, 96px); margin-top: 6px; animation-delay: 140ms; }
.welcome-lines .l3 { font-size: clamp(40px, 5vw, 96px); margin-top: 6px; animation-delay: 280ms; }

@keyframes lineIn {
  from { opacity: 0; transform: translateX(20px); }
  to   { opacity: 1; transform: translateX(0); }
}

/* 底部 ENTER 提示 */
.enter-hint {
  position: static;
  margin-top: clamp(8px, 2vh, 24px);
  display: flex;
  justify-content: center;
  align-items: center;
  opacity: 0;
  animation: enterReveal 500ms ease forwards;
  animation-delay: 0.6s;
}
.enter-text {
  font-size: 22px;
  color: #1f2937; /* 深色，提升对比 */
  letter-spacing: 12px;
  font-weight: 900;
  opacity: 0.98;
  padding: 8px 18px;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.78);
  box-shadow: 0 6px 22px rgba(0,0,0,0.18);
  animation: enterPulse 1.2s ease-in-out infinite;
  animation-delay: 1.6s; /* 等三行字出现后再开始闪动 */
}
@keyframes enterPulse {
  0%, 100% { opacity: 0.2; transform: translateY(0) scale(0.98); }
  50% { opacity: 1; transform: translateY(-2px) scale(1.08); }
}
@keyframes enterGlow {
  0% { box-shadow: 0 0 0 rgba(31,41,55,0.0), 0 6px 22px rgba(0,0,0,0.18); }
  100% { box-shadow: 0 0 16px rgba(31,41,55,0.38), 0 6px 22px rgba(0,0,0,0.18); }
}
@keyframes caretBlink {
  0%, 49% { opacity: 0; }
  50%, 100% { opacity: 1; }
}

@keyframes enterReveal {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 登录窗体出现过渡 */
.fade-up-enter-active, .fade-up-leave-active { transition: all 320ms ease; }
.fade-up-enter-from, .fade-up-leave-to { opacity: 0; transform: translateY(10px); }
</style>
