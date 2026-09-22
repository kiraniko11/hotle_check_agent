<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { House, SwitchButton } from '@element-plus/icons-vue'

import { adminNavItems } from '../../admin/options'
import { useAdminAuthStore } from '../../stores/adminAuth'

const route = useRoute()
const router = useRouter()
const adminAuthStore = useAdminAuthStore()
const stats = ref({})

// 管理员头像旁展示中文称呼，避免直接暴露英文账号名。
const adminDisplayName = computed(() => {
  const profile = adminAuthStore.user || {}
  const realName = `${profile.last_name || ''}${profile.first_name || ''}`.trim()
  return realName || '系统管理员'
})

const statCards = computed(() => [
  { label: '用户', value: stats.value.users || 0 },
])

function handleStatsLoaded(value) {
  stats.value = value || {}
}

function handleLogout() {
  adminAuthStore.logout()
  router.push('/admin/login')
}
</script>

<template>
  <main class="admin-layout">
    <aside class="admin-sidebar">
      <div class="admin-brand" @click="router.push('/admin/users')">
        <span class="brand-mark">
          <el-icon><House /></el-icon>
        </span>
        <div>
          <strong>酒店管理后台</strong>
          <small>运营管理台</small>
        </div>
      </div>

      <nav class="admin-nav" aria-label="管理员导航">
        <router-link
          v-for="item in adminNavItems"
          :key="item.key"
          :to="item.route"
          class="admin-nav-link"
          active-class="active"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>

      <button class="logout-link" type="button" @click="handleLogout">
        <el-icon><SwitchButton /></el-icon>
        <span>退出后台</span>
      </button>
    </aside>

    <section class="admin-content">
      <header class="admin-topbar">
        <div>
          <span class="top-eyebrow">后台总览</span>
          <h2>{{ route.meta.title || '管理后台' }}</h2>
        </div>
        <div class="admin-user-chip">
          <el-avatar :src="adminAuthStore.user?.avatar_url" :size="36">
            管
          </el-avatar>
          <div>
            <strong>{{ adminDisplayName }}</strong>
            <small>后台账号</small>
          </div>
        </div>
      </header>

      <div class="stat-strip">
        <div v-for="item in statCards" :key="item.label" class="stat-pill">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </div>
      </div>

      <router-view @stats-loaded="handleStatsLoaded" />
    </section>
  </main>
</template>

<style scoped>
.admin-layout {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 264px minmax(0, 1fr);
  background: #f3f5f8;
  color: #172033;
}

.admin-sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  background: #ffffff;
  border-right: 1px solid #e5e7eb;
  padding: 22px 18px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  box-shadow: 16px 0 40px rgba(15, 23, 42, 0.04);
}

.admin-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  padding: 6px 4px 18px;
  border-bottom: 1px solid #edf0f4;
}

.brand-mark {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  background: #1f2937;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.admin-brand strong,
.admin-brand small,
.admin-user-chip strong,
.admin-user-chip small {
  display: block;
}

.admin-brand strong {
  font-size: 16px;
  font-weight: 900;
  white-space: nowrap;
}

.admin-brand small,
.admin-user-chip small {
  margin-top: 3px;
  color: #7b8495;
  font-size: 12px;
}

.admin-nav {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.admin-nav-link,
.logout-link {
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 0 13px;
  color: #4b5563;
  text-decoration: none;
  font-size: 14px;
  font-weight: 800;
  border: 0;
  background: transparent;
  cursor: pointer;
  transition: background 0.2s ease, color 0.2s ease, transform 0.2s ease;
}

.admin-nav-link:hover,
.admin-nav-link.active {
  background: #eef2ff;
  color: #3730a3;
}

.admin-nav-link.active {
  box-shadow: inset 3px 0 0 #6366f1;
}

.logout-link {
  margin-top: auto;
  color: #b42318;
}

.logout-link:hover {
  background: #fff1f0;
}

.admin-content {
  min-width: 0;
  padding: 26px 30px 34px;
}

.admin-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.top-eyebrow {
  color: #6366f1;
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 1.5px;
  text-transform: uppercase;
}

.admin-topbar h2 {
  margin: 5px 0 0;
  font-size: 24px;
  font-weight: 900;
}

.admin-user-chip {
  height: 48px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 14px 6px 6px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
}

.admin-user-chip strong {
  font-size: 13px;
  font-weight: 900;
}

.stat-strip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}

.stat-pill {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 15px 18px;
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}

.stat-pill span {
  color: #697386;
  font-size: 13px;
  font-weight: 800;
}

.stat-pill strong {
  color: #111827;
  font-size: 24px;
  font-weight: 900;
}

@media (max-width: 900px) {
  .admin-layout {
    grid-template-columns: 1fr;
  }

  .admin-sidebar {
    position: relative;
    height: auto;
  }

  .admin-nav {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .stat-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
