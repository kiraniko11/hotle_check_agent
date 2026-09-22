<script setup>
import { useRouter } from 'vue-router'
import { computed } from 'vue'
import {
  ChatDotRound,
  ChatLineRound,
  Collection,
  House,
  Menu as MenuIcon,
  OfficeBuilding,
  SwitchButton,
  Tickets,
  User,
} from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// 顶部导航头像优先展示用户上传图片。
const navAvatarUrl = computed(() => authStore.user?.avatar_url || authStore.user?.avatar || '')

// 用户端主导航。
const navItems = [
  { to: '/dashboard', label: '首页大厅', icon: House },
  { to: '/rooms', label: '客房预订', icon: OfficeBuilding },
  { to: '/ai-chat', label: 'AI 预订助手', icon: ChatDotRound },
  { to: '/orders', label: '我的订单', icon: Tickets },
  { to: '/favorites', label: '我的收藏', icon: Collection },
  { to: '/reviews', label: '酒店点评', icon: ChatLineRound },
]

// 退出登录。
async function handleLogout() {
  try {
    await ElMessageBox.confirm('确认退出当前账号吗？', '退出登录', {
      confirmButtonText: '退出',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  await authStore.logout()
  router.push('/login')
}
</script>

<template>
  <div class="layout-wrapper">
    <!-- 全局置顶毛玻璃导航栏 -->
    <header class="glass-navbar">
      <div class="nav-brand" @click="router.push('/dashboard')">
        <el-icon class="brand-icon"><House /></el-icon>
        <div class="brand-text">
          <span class="brand-title">友家快捷酒店</span>
          <span class="brand-subtitle">干净舒适 价格实在</span>
        </div>
      </div>

      <nav class="nav-links" aria-label="页面导航">
        <router-link
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="nav-link"
          active-class="active"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="nav-actions">
        <div class="user-chip" @click="router.push('/profile')" style="cursor: pointer;" title="进入个人中心">
          <el-avatar :size="30" :src="navAvatarUrl" :icon="User" class="user-avatar" />
          <span class="user-name">{{ authStore.user?.username || '住客' }}</span>
          <span class="user-role">{{ authStore.user?.role === 'admin' ? '管理员' : '会员' }}</span>
        </div>
        <el-button :icon="SwitchButton" circle plain type="danger" class="logout-btn" @click="handleLogout" title="退出登录" />
      </div>
    </header>

    <!-- 路由页面渲染区 -->
    <div class="main-content">
      <router-view />
    </div>

    <footer class="glass-footer">
      <span>友家快捷酒店 · 在线预订系统</span>
      <span class="footer-dot">·</span>
      <span>Django + Vue 3 + LangGraph 智能体实战项目</span>
    </footer>
  </div>
</template>

<style scoped>
.layout-wrapper {
  min-height: 100vh;
  background-color: #f4f7fb;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  width: 100%;
  padding-top: 72px;
}

/* 顶部毛玻璃导航栏 */
.glass-navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 72px;
  background: rgba(244, 247, 251, 0.9);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(22, 50, 79, 0.15);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  z-index: 2500;
  box-shadow: 0 4px 30px rgba(22, 50, 79, 0.03);
  gap: 16px;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  flex-shrink: 0;
}

.brand-icon {
  font-size: 26px;
  color: #16324f;
}

.brand-text {
  display: flex;
  flex-direction: column;
}

.brand-title {
  font-size: 16px;
  font-weight: 800;
  color: #1a2b40;
  letter-spacing: 0.5px;
  white-space: nowrap;
}

.brand-subtitle {
  font-size: 9px;
  font-weight: 600;
  color: #4f8ef7;
  letter-spacing: 1.5px;
}

.nav-links {
  display: flex;
  gap: 26px;
  flex-wrap: nowrap;
}

.nav-link {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 13.5px;
  font-weight: 600;
  color: #46566b;
  transition: color 0.3s ease;
  position: relative;
  padding: 6px 0;
  text-decoration: none;
  white-space: nowrap;
}

.nav-link .el-icon {
  font-size: 15px;
}

.nav-link:hover, .nav-link.active {
  color: #16324f;
}

.nav-link.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background-color: #16324f;
  border-radius: 2px;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-shrink: 0;
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(22, 50, 79, 0.06);
  padding: 4px 14px 4px 4px;
  border-radius: 30px;
  border: 1px solid rgba(22, 50, 79, 0.12);
}

.user-name {
  font-size: 13px;
  font-weight: 700;
  color: #1a2b40;
}

.user-role {
  font-size: 10px;
  background: #16324f;
  color: #ffffff;
  padding: 1px 6px;
  border-radius: 10px;
  font-weight: 700;
}

.logout-btn {
  border-color: rgba(231, 76, 60, 0.2) !important;
  background: transparent !important;
  color: #e74c3c !important;
}

.logout-btn:hover {
  background: #e74c3c !important;
  color: #ffffff !important;
}

/* 页脚 */
.glass-footer {
  margin-top: 60px;
  padding: 24px 32px 32px;
  text-align: center;
  font-size: 12px;
  color: #9aa5a0;
  border-top: 1px solid rgba(22, 50, 79, 0.08);
  letter-spacing: 0.4px;
}

.footer-dot {
  margin: 0 8px;
  color: #4f8ef7;
}

@media (max-width: 1180px) {
  .glass-navbar {
    padding: 0 18px;
  }

  .nav-links {
    gap: 16px;
  }

  .nav-link span {
    display: none;
  }
}

@media (max-width: 720px) {
  .brand-text {
    display: none;
  }

  .user-name,
  .user-role {
    display: none;
  }
}
</style>
