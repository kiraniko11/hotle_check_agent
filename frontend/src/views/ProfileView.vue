<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Collection, Lock, Tickets, User } from '@element-plus/icons-vue'

import { changePassword, fetchProfile, updateProfile } from '../api/auth'
import { getUserBookings, getUserFavorites } from '../api/rooms'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const profileLoading = ref(true)
const savingProfile = ref(false)
const avatarUploading = ref(false)
const pwdDialogVisible = ref(false)
const pwdLoading = ref(false)

const orderCount = ref(0)
const favoriteCount = ref(0)
const statsLoading = ref(true)

const profileForm = reactive({
  last_name: '',
  first_name: '',
  email: '',
  mobile: '',
})

const pwdFormRef = ref()
const pwdForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

function validateNewPassword(rule, value, callback) {
  if (value && value === pwdForm.old_password) {
    callback(new Error('新密码不能与原密码相同'))
    return
  }
  callback()
}

function validateConfirmPassword(rule, value, callback) {
  if (value !== pwdForm.new_password) {
    callback(new Error('两次输入的新密码不一致'))
    return
  }
  callback()
}

const pwdRules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '新密码至少 6 个字符', trigger: 'blur' },
    { validator: validateNewPassword, trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' },
  ],
}

// 顶部展示的完整姓名。
const displayName = computed(() => {
  const realName = `${profileForm.last_name}${profileForm.first_name}`.trim()
  return realName || authStore.user?.username || '住客'
})

const avatarUrl = computed(() => authStore.user?.avatar_url || authStore.user?.avatar || '')

// 智能体自动填充提示。
const autoFillReady = computed(() => Boolean(displayName.value && profileForm.mobile))

// 同步资料到本地表单与登录态。
function syncProfile(data) {
  profileForm.last_name = data.last_name || ''
  profileForm.first_name = data.first_name || ''
  profileForm.email = data.email || ''
  profileForm.mobile = data.mobile || ''
  authStore.user = data
  localStorage.setItem('user', JSON.stringify(data))
}

// 加载用户资料。
async function loadProfile() {
  profileLoading.value = true
  try {
    const response = await fetchProfile()
    syncProfile(response.data)
  } finally {
    profileLoading.value = false
  }
}

// 加载订单数与收藏数统计。
async function loadStats() {
  statsLoading.value = true
  try {
    const [orderRes, favRes] = await Promise.all([getUserBookings(), getUserFavorites()])
    if (orderRes.data?.code === 200) orderCount.value = orderRes.data.data.length
    if (favRes.data?.code === 200) favoriteCount.value = favRes.data.data.length
  } finally {
    statsLoading.value = false
  }
}

// 保存资料修改。
async function handleSaveProfile() {
  savingProfile.value = true
  try {
    const response = await updateProfile({
      last_name: profileForm.last_name,
      first_name: profileForm.first_name,
      email: profileForm.email,
      mobile: profileForm.mobile,
    })
    syncProfile(response.data)
    ElMessage.success('个人资料已更新')
  } finally {
    savingProfile.value = false
  }
}

// 上传头像前校验文件类型和大小。
function beforeAvatarUpload(file) {
  const allowTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
  if (!allowTypes.includes(file.type)) {
    ElMessage.warning('仅支持 JPG、PNG、WEBP 或 GIF 图片')
    return false
  }
  if (file.size > 2 * 1024 * 1024) {
    ElMessage.warning('头像大小不能超过 2MB')
    return false
  }
  return true
}

// 调用资料接口上传头像，并同步展示最新头像。
async function handleAvatarUpload({ file }) {
  avatarUploading.value = true
  try {
    const formData = new FormData()
    formData.append('avatar', file)
    const response = await updateProfile(formData)
    syncProfile(response.data)
    ElMessage.success('头像已更新')
  } finally {
    avatarUploading.value = false
  }
}

// 提交密码修改，并在成功后强制重新登录。
async function handleChangePassword() {
  const valid = await pwdFormRef.value.validate().catch(() => false)
  if (!valid) return

  pwdLoading.value = true
  try {
    const response = await changePassword(pwdForm)
    if (response.data && response.data.code === 200) {
      ElMessage.success(response.data.msg || '密码修改成功，请重新登录')
      pwdDialogVisible.value = false
      // 密码修改后强制重新登录。
      setTimeout(() => {
        authStore.logout()
        router.push('/login')
      }, 1500)
    }
  } finally {
    pwdLoading.value = false
  }
}

onMounted(() => {
  loadProfile()
  loadStats()
})
</script>

<template>
  <main class="profile-page">
    <div class="profile-body">
      <!-- 资料头卡 -->
      <section v-loading="profileLoading" class="profile-hero">
        <el-upload
          class="avatar-uploader"
          :show-file-list="false"
          :before-upload="beforeAvatarUpload"
          :http-request="handleAvatarUpload"
          accept="image/*"
        >
          <div class="avatar-wrapper" :class="{ uploading: avatarUploading }">
            <el-avatar :size="94" :src="avatarUrl" :icon="User" />
            <span class="avatar-hint">{{ avatarUploading ? '上传中…' : '更换头像' }}</span>
          </div>
        </el-upload>

        <div class="hero-info">
          <h1>{{ displayName }}</h1>
          <p class="hero-username">账号：{{ authStore.user?.username }}</p>
          <span class="role-chip">{{ authStore.user?.role === 'admin' ? '系统管理员' : '会员' }}</span>
        </div>

        <div class="hero-stats">
          <div class="hero-stat">
            <el-icon><Tickets /></el-icon>
            <div>
              <strong>{{ orderCount }}</strong>
              <span>预订订单</span>
            </div>
          </div>
          <div class="hero-stat">
            <el-icon><Collection /></el-icon>
            <div>
              <strong>{{ favoriteCount }}</strong>
              <span>收藏房型</span>
            </div>
          </div>
        </div>
      </section>

      <div class="profile-grid">
        <!-- 资料编辑 -->
        <section class="profile-card">
          <div class="card-head">
            <h2>基本资料</h2>
            <span class="card-tip">用于预订登记与 AI 助手自动填单</span>
          </div>

          <el-form label-position="top" class="profile-form">
            <div class="form-row">
              <el-form-item label="姓">
                <el-input v-model="profileForm.last_name" maxlength="30" placeholder="如：王" />
              </el-form-item>
              <el-form-item label="名">
                <el-input v-model="profileForm.first_name" maxlength="30" placeholder="如：小明" />
              </el-form-item>
            </div>

            <div class="form-row">
              <el-form-item label="手机号">
                <el-input v-model="profileForm.mobile" maxlength="11" placeholder="11 位手机号" />
              </el-form-item>
              <el-form-item label="邮箱">
                <el-input v-model="profileForm.email" maxlength="120" placeholder="用于接收确认邮件" />
              </el-form-item>
            </div>

            <div class="auto-fill-hint" :class="{ ready: autoFillReady }">
              {{ autoFillReady
                ? '资料完整：AI 预订助手在下单时会自动使用该姓名与手机号，无需重复填写。'
                : '补全姓名与手机号后，AI 预订助手可自动完成下单登记。' }}
            </div>

            <el-button class="save-btn" :loading="savingProfile" @click="handleSaveProfile">
              保存资料
            </el-button>
          </el-form>
        </section>

        <!-- 安全设置 -->
        <section class="profile-card">
          <div class="card-head">
            <h2>账号安全</h2>
            <span class="card-tip">定期更换密码可提升账号安全性</span>
          </div>

          <ul class="security-list">
            <li>
              <el-icon><Lock /></el-icon>
              <div>
                <strong>登录密码</strong>
                <span>建议使用 6 位以上，包含字母与数字的组合</span>
              </div>
              <el-button plain size="small" @click="pwdDialogVisible = true">修改</el-button>
            </li>
            <li>
              <el-icon><User /></el-icon>
              <div>
                <strong>登录账号</strong>
                <span>{{ authStore.user?.username }} · 手机号 {{ authStore.user?.mobile }}</span>
              </div>
            </li>
          </ul>

          <div class="quick-links">
            <el-button plain @click="router.push('/orders')">查看我的订单</el-button>
            <el-button plain @click="router.push('/favorites')">查看我的收藏</el-button>
            <el-button plain @click="router.push('/ai-chat')">进入 AI 助手</el-button>
          </div>
        </section>
      </div>
    </div>

    <!-- 修改密码弹窗 -->
    <el-dialog v-model="pwdDialogVisible" title="修改登录密码" width="460px" :close-on-click-modal="false">
      <el-form ref="pwdFormRef" :model="pwdForm" :rules="pwdRules" label-position="top">
        <el-form-item label="原密码" prop="old_password">
          <el-input v-model="pwdForm.old_password" type="password" show-password placeholder="请输入当前密码" />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="pwdForm.new_password" type="password" show-password placeholder="至少 6 个字符" />
        </el-form-item>
        <el-form-item label="确认新密码" prop="confirm_password">
          <el-input v-model="pwdForm.confirm_password" type="password" show-password placeholder="请再次输入新密码" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="pwdDialogVisible = false">取消</el-button>
        <el-button class="save-btn" :loading="pwdLoading" @click="handleChangePassword">
          确认修改
        </el-button>
      </template>
    </el-dialog>
  </main>
</template>

<style scoped>
.profile-page {
  min-height: 100vh;
  background-color: #f4f7fb;
  padding-bottom: 80px;
}

.profile-body {
  max-width: 1100px;
  margin: 0 auto;
  padding: 44px 24px 0;
}

/* 资料头卡 */
.profile-hero {
  background: linear-gradient(120deg, #16324f 0%, #1d3f2c 55%, #2b5540 100%);
  border-radius: 20px;
  padding: 34px 38px;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 26px;
  color: #ffffff;
  box-shadow: 0 18px 40px rgba(22, 50, 79, 0.22);
  margin-bottom: 32px;
}

.avatar-uploader :deep(.el-upload) {
  display: block;
}

.avatar-wrapper {
  position: relative;
  cursor: pointer;
  border-radius: 50%;
  padding: 4px;
  border: 2px solid rgba(79, 142, 247, 0.6);
  transition: border-color 0.3s ease;
}

.avatar-wrapper:hover {
  border-color: #4f8ef7;
}

.avatar-wrapper.uploading {
  opacity: 0.7;
}

.avatar-hint {
  position: absolute;
  left: 50%;
  bottom: -22px;
  transform: translateX(-50%);
  font-size: 11px;
  color: #4f8ef7;
  font-weight: 700;
  white-space: nowrap;
}

.hero-info h1 {
  font-size: 28px;
  font-weight: 800;
  margin: 0 0 8px;
  font-family: 'Georgia', serif;
  letter-spacing: 0.5px;
}

.hero-username {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.66);
  margin: 0 0 12px;
}

.role-chip {
  display: inline-block;
  background: rgba(79, 142, 247, 0.16);
  border: 1px solid rgba(79, 142, 247, 0.5);
  color: #4f8ef7;
  font-size: 11px;
  font-weight: 800;
  padding: 4px 12px;
  border-radius: 20px;
  letter-spacing: 0.6px;
}

.hero-stats {
  display: flex;
  gap: 26px;
}

.hero-stat {
  display: flex;
  align-items: center;
  gap: 12px;
}

.hero-stat .el-icon {
  font-size: 22px;
  color: #4f8ef7;
}

.hero-stat strong {
  display: block;
  font-size: 22px;
  font-weight: 800;
  font-family: 'Georgia', serif;
}

.hero-stat span {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.6);
  font-weight: 700;
}

/* 两栏卡片 */
.profile-grid {
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 26px;
  align-items: start;
}

.profile-card {
  background: #ffffff;
  border: 1px solid rgba(22, 50, 79, 0.08);
  border-radius: 16px;
  padding: 28px 30px;
  box-shadow: 0 10px 30px rgba(22, 50, 79, 0.03);
}

.card-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 20px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(22, 50, 79, 0.06);
}

.card-head h2 {
  font-size: 17px;
  font-weight: 800;
  color: #1a2b40;
  margin: 0;
  font-family: 'Georgia', serif;
}

.card-tip {
  font-size: 11px;
  color: #9fadc0;
  font-weight: 600;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 18px;
}

.auto-fill-hint {
  font-size: 12px;
  line-height: 1.7;
  color: #2f6fd8;
  background: rgba(79, 142, 247, 0.1);
  border: 1px dashed rgba(79, 142, 247, 0.5);
  border-radius: 10px;
  padding: 12px 14px;
  margin-bottom: 18px;
}

.auto-fill-hint.ready {
  color: #1d7a4a;
  background: rgba(39, 174, 96, 0.08);
  border-color: rgba(39, 174, 96, 0.4);
}

.save-btn {
  background: #16324f !important;
  border-color: #16324f !important;
  color: #ffffff !important;
  font-weight: 700;
  height: 42px;
  border-radius: 8px;
  width: 100%;
}

.save-btn:hover {
  background: #1a2b40 !important;
}

/* 安全设置 */
.security-list {
  list-style: none;
  padding: 0;
  margin: 0 0 22px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.security-list li {
  display: flex;
  align-items: center;
  gap: 14px;
  background: #f8fafd;
  border: 1px solid rgba(22, 50, 79, 0.06);
  border-radius: 12px;
  padding: 16px 18px;
}

.security-list li .el-icon {
  font-size: 18px;
  color: #4f8ef7;
  flex-shrink: 0;
}

.security-list li div {
  flex: 1;
  min-width: 0;
}

.security-list strong {
  display: block;
  font-size: 13px;
  font-weight: 800;
  color: #1a2b40;
  margin-bottom: 4px;
}

.security-list span {
  font-size: 12px;
  color: #8494ab;
  word-break: break-all;
}

.quick-links {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

@media (max-width: 992px) {
  .profile-hero {
    grid-template-columns: 1fr;
    text-align: center;
    justify-items: center;
    gap: 30px;
  }

  .hero-stats {
    justify-content: center;
  }

  .profile-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 600px) {
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
