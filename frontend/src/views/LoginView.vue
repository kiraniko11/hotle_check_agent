<script setup>
import { Lock, User } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { reactive, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const formRef = ref()

const form = reactive({
  account: '',
  password: '',
})

const rules = {
  account: [{ required: true, message: '请输入用户名或手机号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)

  if (!valid) {
    return
  }

  await authStore.login(form)
  ElMessage.success('登录成功')
  router.push(route.query.redirect || '/dashboard')
}
</script>

<template>
  <main class="auth-page">
    <section class="auth-visual">
      <img src="../assets/hotel-auth-hero.png" alt="酒店大堂" />
    </section>

    <section class="auth-panel" aria-label="登录表单">
      <div class="auth-box">
        <p class="auth-eyebrow">Hotel Booking</p>
        <h1>酒店预订系统</h1>
        <p class="auth-subtitle">登录后管理个人资料，并继续完成酒店预订流程。</p>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          class="auth-form"
          label-position="top"
          @submit.prevent="handleSubmit"
        >
          <el-form-item label="账号" prop="account">
            <el-input
              v-model.trim="form.account"
              :prefix-icon="User"
              autocomplete="username"
              placeholder="请输入用户名或手机号"
              size="large"
            />
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input
              v-model="form.password"
              :prefix-icon="Lock"
              autocomplete="current-password"
              placeholder="请输入密码"
              show-password
              size="large"
              type="password"
              @keyup.enter="handleSubmit"
            />
          </el-form-item>

          <el-button
            class="auth-submit"
            native-type="submit"
            size="large"
            type="primary"
            :loading="authStore.loading"
          >
            登录
          </el-button>
        </el-form>

        <p class="auth-switch">
          还没有账号？
          <RouterLink to="/register">立即注册</RouterLink>
        </p>
      </div>
    </section>
  </main>
</template>
