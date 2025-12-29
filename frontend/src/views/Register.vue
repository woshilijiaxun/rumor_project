<template>
  <AuthLayout noDark>
    <h2>用户注册</h2>

    <div class="form-group">
      <input v-model="username" placeholder="用户名（至少3个字符）" class="form-input" />
    </div>
    <div class="form-group">
      <input v-model="password" type="password" placeholder="密码（至少6个字符）" class="form-input" />
    </div>
    <div class="form-group">
      <input v-model="email" type="email" placeholder="邮箱（可选）" class="form-input" />
    </div>

    <button @click="handleRegister" class="auth-btn">注册</button>
    <p v-if="message" :class="{'success-msg': isSuccess, 'error-msg': !isSuccess}">{{ message }}</p>
    <p class="link-text">
      已有账号？<a @click="goToLogin">去登录</a>
    </p>
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
      email: '',
      message: '',
      isSuccess: false
    }
  },
  methods: {
    handleRegister() {
      if (!this.username || !this.password) {
        this.message = '用户名和密码不能为空'
        this.isSuccess = false
        return
      }

      if (this.username.length < 3) {
        this.message = '用户名至少需要3个字符'
        this.isSuccess = false
        return
      }

      if (this.password.length < 6) {
        this.message = '密码至少需要6个字符'
        this.isSuccess = false
        return
      }

      axios.post('/api/register', {
        username: this.username,
        password: this.password,
        email: this.email
      })
      .then(response => {
        this.message = response.data.message
        this.isSuccess = response.data.status === 'success'
        if (this.isSuccess) {
          setTimeout(() => {
            this.$router.push('/login')
          }, 1200)
        }
      })
      .catch(error => {
        this.isSuccess = false
        if (error.response && error.response.data) {
          this.message = error.response.data.message || '注册失败'
        } else {
          this.message = '注册失败: ' + error.message
        }
      })
    },
    goToLogin() {
      this.$router.push('/login')
    }
  }
}
</script>

<style scoped>
/* 样式统一在 AuthLayout 中维护，这里仅保留页面特有样式（当前无需） */
</style>
