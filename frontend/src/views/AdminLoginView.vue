<script setup>
import { reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock, Right, UserFilled } from '@element-plus/icons-vue'

import { useAdminAuthStore } from '../stores/adminAuth'

const route = useRoute()
const router = useRouter()
const adminAuthStore = useAdminAuthStore()

const form = reactive({
  account: '',
  password: '',
})

async function handleLogin() {
  if (!form.account || !form.password) {
    ElMessage.warning('请输入管理员账号和密码')
    return
  }

  try {
    await adminAuthStore.login({
      account: form.account,
      password: form.password,
    })
    ElMessage.success('管理员登录成功')
    router.push(route.query.redirect || '/admin/users')
  } catch (err) {
    const message = err.response?.data?.detail || err.response?.data?.msg || '管理员登录失败'
    ElMessage.error(message)
  }
}
</script>

<template>
  <main class="admin-login-page">
    <section class="login-shell">
      <div class="login-copy">
        <span class="copy-kicker">酒店管理后台</span>
        <h1>后台运营中心</h1>
        <p>集中维护客房、订单、用户、留言与评价，让酒店预订系统保持清晰可控。</p>
        <div class="copy-metrics">
          <div>
            <strong>7</strong>
            <span>管理模块</span>
          </div>
          <div>
            <strong>增删改查</strong>
            <span>完整维护</span>
          </div>
          <div>
            <strong>令牌</strong>
            <span>角色鉴权</span>
          </div>
        </div>
      </div>

      <div class="login-card">
        <div class="login-card-head">
          <span class="admin-dot"></span>
          <div>
            <h2>管理员登录</h2>
            <p>仅允许管理员角色进入后台</p>
          </div>
        </div>

        <label class="form-field">
          <span>账号</span>
          <el-input
            v-model="form.account"
            :prefix-icon="UserFilled"
            placeholder="用户名或手机号"
            size="large"
            @keydown.enter.prevent="handleLogin"
          />
        </label>
        <label class="form-field">
          <span>密码</span>
          <el-input
            v-model="form.password"
            :prefix-icon="Lock"
            placeholder="管理员密码"
            size="large"
            type="password"
            show-password
            @keydown.enter.prevent="handleLogin"
          />
        </label>

        <el-button
          class="login-btn"
          type="primary"
          size="large"
          :icon="Right"
          :loading="adminAuthStore.loading"
          @click="handleLogin"
        >
          进入后台
        </el-button>
        <button class="text-link" type="button" @click="router.push('/login')">返回用户端登录</button>
      </div>
    </section>
  </main>
</template>

<style scoped>
.admin-login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 42px 22px;
  background:
    radial-gradient(circle at 18% 18%, rgba(99, 102, 241, 0.16), transparent 28%),
    radial-gradient(circle at 84% 18%, rgba(14, 165, 233, 0.16), transparent 28%),
    linear-gradient(135deg, #eef2ff 0%, #f8fafc 48%, #ecfeff 100%);
}

.login-shell {
  width: min(1060px, 100%);
  display: grid;
  grid-template-columns: minmax(0, 1fr) 420px;
  gap: 28px;
  align-items: stretch;
}

.login-copy,
.login-card {
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 22px;
  box-shadow: 0 28px 70px rgba(15, 23, 42, 0.12);
  backdrop-filter: blur(20px);
}

.login-copy {
  padding: 56px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 520px;
}

.copy-kicker {
  color: #4f46e5;
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 1.8px;
  text-transform: uppercase;
}

.login-copy h1 {
  margin: 18px 0 0;
  color: #111827;
  font-size: 44px;
  line-height: 1.12;
  font-weight: 950;
}

.login-copy p {
  width: min(520px, 100%);
  margin: 18px 0 0;
  color: #5b6475;
  font-size: 16px;
  line-height: 1.9;
}

.copy-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.copy-metrics div {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  padding: 18px;
}

.copy-metrics strong,
.copy-metrics span {
  display: block;
}

.copy-metrics strong {
  color: #111827;
  font-size: 24px;
  font-weight: 950;
}

.copy-metrics span {
  margin-top: 4px;
  color: #7b8495;
  font-size: 12px;
  font-weight: 800;
}

.login-card {
  padding: 36px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 22px;
}

.login-card-head {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 8px;
}

.admin-dot {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  background: #1f2937;
  box-shadow: inset 0 0 0 8px #6366f1;
  flex-shrink: 0;
}

.login-card h2 {
  margin: 0;
  color: #111827;
  font-size: 24px;
  font-weight: 950;
}

.login-card p {
  margin: 4px 0 0;
  color: #7b8495;
  font-size: 13px;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 9px;
  color: #374151;
  font-size: 13px;
  font-weight: 900;
}

.login-btn {
  height: 48px;
  background: #1f2937 !important;
  border-color: #1f2937 !important;
  font-weight: 900;
}

.text-link {
  border: 0;
  background: transparent;
  color: #4f46e5;
  font-size: 13px;
  font-weight: 900;
  cursor: pointer;
}

@media (max-width: 860px) {
  .login-shell {
    grid-template-columns: 1fr;
  }

  .login-copy {
    min-height: 360px;
    padding: 34px;
  }

  .copy-metrics {
    margin-top: 30px;
  }
}
</style>
