<script setup>
import { Iphone, Lock, User } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { reactive, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const formRef = ref()

const form = reactive({
  username: '',
  mobile: '',
  password: '',
  confirm_password: '',
})

function validateConfirmPassword(rule, value, callback) {
  if (value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
    return
  }

  callback()
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 30, message: '用户名长度为 3 到 30 个字符', trigger: 'blur' },
  ],
  mobile: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 个字符', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' },
  ],
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)

  if (!valid) {
    return
  }

  await authStore.register(form)
  ElMessage.success('注册成功')
  router.push('/dashboard')
}
</script>

<template>
  <main class="auth-page">
    <section class="auth-visual">
      <img src="../assets/hotel-auth-hero.png" alt="酒店大堂" />
    </section>

    <section class="auth-panel" aria-label="注册表单">
      <div class="auth-box">
        <p class="auth-eyebrow">Create Account</p>
        <h1>创建预订账号</h1>
        <p class="auth-subtitle">使用用户名和手机号注册，后续可直接完成酒店预订。</p>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          class="auth-form"
          label-position="top"
          @submit.prevent="handleSubmit"
        >
          <el-form-item label="用户名" prop="username">
            <el-input
              v-model.trim="form.username"
              :prefix-icon="User"
              autocomplete="username"
              placeholder="请输入用户名"
              size="large"
            />
          </el-form-item>

          <el-form-item label="手机号" prop="mobile">
            <el-input
              v-model.trim="form.mobile"
              :prefix-icon="Iphone"
              autocomplete="tel"
              maxlength="11"
              placeholder="请输入手机号"
              size="large"
            />
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input
              v-model="form.password"
              :prefix-icon="Lock"
              autocomplete="new-password"
              placeholder="请输入密码"
              show-password
              size="large"
              type="password"
            />
          </el-form-item>

          <el-form-item label="确认密码" prop="confirm_password">
            <el-input
              v-model="form.confirm_password"
              :prefix-icon="Lock"
              autocomplete="new-password"
              placeholder="请再次输入密码"
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
            注册并登录
          </el-button>
        </el-form>

        <p class="auth-switch">
          已有账号？
          <RouterLink to="/login">返回登录</RouterLink>
        </p>
      </div>
    </section>
  </main>
</template>
