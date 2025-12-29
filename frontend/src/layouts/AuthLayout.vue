<template>
  <div class="auth-wrapper" :class="wrapperClasses">
    <div class="auth-background" :style="{ backgroundImage: `url(${background})` }" />
    <div class="auth-right">
      <div v-if="$slots.header" class="auth-header">
        <slot name="header" />
      </div>
      <div v-if="showContainer" class="auth-container">
        <slot />
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AuthLayout',
  props: {
    background: { type: String, default: '/images/sys_img.jpg' },
    noDark: { type: Boolean, default: false },
    noRightGradient: { type: Boolean, default: false },
    showContainer: { type: Boolean, default: true }
  },
  computed: {
    wrapperClasses() {
      return {
        'no-dark': this.noDark,
        'no-right-gradient': this.noRightGradient
      }
    }
  }
}
</script>

<style scoped>
.auth-wrapper {
  position: relative;
  min-height: 100dvh;
  height: 100vh;
  width: 100%;
  padding-right: 0;
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: flex-end; /* 让内容靠右居中 */
  
}

/* 全屏背景图片 */
.auth-background {
  position: absolute;
  inset: 0;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  z-index: 0;
}

/* 全局轻微暗化，便于阅读（默认开启，可通过 noDark 关闭） */
.auth-background::after {
  content: '';
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.15);
}

.no-dark .auth-background::after {
  background: none;
}

/* 右侧区域：用于承载渐变/半透明效果（默认开启，可通过 noRightGradient 关闭） */
.auth-right {
  position: relative;
  z-index: 1;
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: flex-end;
  padding: clamp(16px, 4vw, 40px);
}

.auth-right::before {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: radial-gradient(60% 50% at 85% 50%, rgba(255, 255, 255, 0.55) 0%, rgba(255, 255, 255, 0.35) 45%, rgba(255, 255, 255, 0.15) 70%, rgba(255, 255, 255, 0) 100%),
              linear-gradient(90deg, rgba(0, 0, 0, 0) 0%, rgba(0, 0, 0, 0.20) 100%);
}

/* 右侧顶部插槽容器，配合欢迎覆盖层使用 */
.auth-header {
  position: absolute;
  inset: 0;
  width: 100%;
  display: flex;
  justify-content: flex-end;
  z-index: 2;
  pointer-events: none; /* 允许子元素接收点击，容器本身不阻挡 */
}
.auth-header > * {
  width: clamp(280px, 28vw, 360px);
  pointer-events: auto;
}

.no-right-gradient .auth-right::before {
  background: none;
}

/* 卡片容器：毛玻璃 + 半透明 */
.auth-container {
  background: rgba(255, 255, 255, 0.22);
  -webkit-backdrop-filter: blur(10px) saturate(140%);
  backdrop-filter: blur(10px) saturate(140%);
  border: 1px solid rgba(255, 255, 255, 0.35);
  padding: clamp(24px, 3vw, 40px);
  border-radius: 16px;
  width: clamp(280px, 28vw, 360px);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.18);
  text-align: center;
  color: #0f172a; /* 默认文字颜色 */
}

/* 通过深度选择器，给插槽内元素提供统一样式 */
.auth-container :deep(h2) {
  margin: 0 0 10px 0;
  color: #0f172a;
  font-weight: 700;
  font-size: 28px;
}

.auth-container :deep(.form-group) {
  display: flex;
  flex-direction: column;
  margin-bottom: 16px;
}

.auth-container :deep(.form-input) {
  width: 100%;
  max-width: 100%;
  box-sizing: border-box; /* 防止因为内边距和边框导致溢出 */
  padding: 14px 16px;
  border: 2px solid rgba(255, 255, 255, 0.5);
  border-radius: 10px;
  font-size: 16px;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.6);
}

.auth-container :deep(.form-input:focus) {
  border-color: #667eea;
  outline: none;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.15);
  background: rgba(255, 255, 255, 0.85);
}

.auth-container :deep(.form-input::placeholder) {
  color: #777;
}

.auth-container :deep(.auth-btn) {
  width: 100%;
  padding: 14px 0;
  background-color: #2563eb; /* 主题蓝 */
  border: none;
  border-radius: 10px;
  color: white;
  font-size: 18px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 6px;
}

.auth-container :deep(.auth-btn:hover) {
  background-color: #1d4ed8; /* 悬停更深蓝 */
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(37, 99, 235, 0.45);
}

.auth-container :deep(.success-msg) {
  color: #27ae60;
  font-weight: 600;
  margin-top: 10px;
  padding: 10px;
  background: #d5f4e6;
  border-radius: 8px;
}

.auth-container :deep(.error-msg) {
  color: #e74c3c;
  font-weight: 600;
  margin-top: 10px;
  padding: 10px;
  background: #fadbd8;
  border-radius: 8px;
}

.auth-container :deep(.link-text) {
  margin-top: 15px;
  color: #444;
  font-size: 14px;
}

.auth-container :deep(.link-text a) {
  color: #667eea;
  cursor: pointer;
  text-decoration: none;
  font-weight: 600;
  transition: color 0.3s ease;
}

.auth-container :deep(.link-text a:hover) {
  color: #764ba2;
  text-decoration: underline;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .auth-wrapper {
    justify-content: center; /* 小屏幕居中显示 */
  }

  .auth-right {
    justify-content: center;
  }

  .auth-container {
    padding: 36px 28px;
    max-width: 92vw;
  }

  .auth-container :deep(h2) {
    font-size: 28px;
  }
}
</style>
