import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useAdminAuthStore } from '../stores/adminAuth'

// 导入页面组件
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import AdminLoginView from '../views/AdminLoginView.vue'
import DashboardView from '../views/DashboardView.vue'
import RoomsView from '../views/RoomsView.vue'
import RoomDetailView from '../views/RoomDetailView.vue'
import MyOrdersView from '../views/MyOrdersView.vue'
import MyFavoritesView from '../views/MyFavoritesView.vue'
import ReviewBoardView from '../views/ReviewBoardView.vue'
import ProfileView from '../views/ProfileView.vue'
import AiChatView from '../views/AiChatView.vue'

// 导入管理端页面组件
import UserManagementView from '../views/admin/UserManagementView.vue'
import RoomTypeManagementView from '../views/admin/RoomTypeManagementView.vue'
import RoomManagementView from '../views/admin/RoomManagementView.vue'
import BookingManagementView from '../views/admin/BookingManagementView.vue'
import FeedbackManagementView from '../views/admin/FeedbackManagementView.vue'
import ReviewManagementView from '../views/admin/ReviewManagementView.vue'
import FavoriteManagementView from '../views/admin/FavoriteManagementView.vue'

// 导入布局组件
import MainLayout from '../components/MainLayout.vue'
import AdminLayout from '../components/admin/AdminLayout.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { guestOnly: true },
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView,
      meta: { guestOnly: true },
    },
    {
      path: '/admin/login',
      name: 'admin-login',
      component: AdminLoginView,
      meta: { adminGuestOnly: true },
    },
    {
      path: '/',
      component: MainLayout,
      redirect: '/dashboard',
      meta: { requiresAuth: true },
      children: [
        {
          path: 'dashboard',
          name: 'dashboard',
          component: DashboardView,
        },
        {
          path: 'rooms',
          name: 'rooms',
          component: RoomsView,
        },
        {
          path: 'rooms/:id',
          name: 'room-detail',
          component: RoomDetailView,
        },
        {
          path: 'orders',
          name: 'orders',
          component: MyOrdersView,
        },
        {
          path: 'favorites',
          name: 'favorites',
          component: MyFavoritesView,
        },
        {
          path: 'reviews',
          name: 'reviews',
          component: ReviewBoardView,
        },
        {
          path: 'profile',
          name: 'profile',
          component: ProfileView,
        },
        {
          path: 'ai-chat',
          name: 'ai-chat',
          component: AiChatView,
        },
      ],
    },
    {
      path: '/admin',
      component: AdminLayout,
      redirect: '/admin/users',
      meta: { requiresAdmin: true },
      children: [
        {
          path: 'users',
          name: 'admin-users',
          component: UserManagementView,
          meta: { title: '用户管理' },
        },
        {
          path: 'room-types',
          name: 'admin-room-types',
          component: RoomTypeManagementView,
          meta: { title: '房型管理' },
        },
        {
          path: 'rooms',
          name: 'admin-rooms',
          component: RoomManagementView,
          meta: { title: '房间管理' },
        },
        {
          path: 'bookings',
          name: 'admin-bookings',
          component: BookingManagementView,
          meta: { title: '订单管理' },
        },
        {
          path: 'feedbacks',
          name: 'admin-feedbacks',
          component: FeedbackManagementView,
          meta: { title: '留言管理' },
        },
        {
          path: 'reviews',
          name: 'admin-reviews',
          component: ReviewManagementView,
          meta: { title: '评价管理' },
        },
        {
          path: 'favorites',
          name: 'admin-favorites',
          component: FavoriteManagementView,
          meta: { title: '收藏管理' },
        },
      ],
    },
    {
      // 未匹配到任何路由时回到首页大厅。
      path: '/:pathMatch(.*)*',
      redirect: '/dashboard',
    },
  ],
})

// 路由守卫
router.beforeEach(async (to) => {
  const authStore = useAuthStore()
  const adminAuthStore = useAdminAuthStore()

  // 管理员路由守卫
  if (to.meta.requiresAdmin) {
    if (adminAuthStore.token && !adminAuthStore.user) {
      await adminAuthStore.loadProfile()
    }

    if (!adminAuthStore.isAuthenticated) {
      return { name: 'admin-login', query: { redirect: to.fullPath } }
    }

    if (adminAuthStore.user?.role !== 'admin') {
      adminAuthStore.clearSession()
      return { name: 'admin-login' }
    }
  }

  if (to.meta.adminGuestOnly && adminAuthStore.isAuthenticated) {
    return { name: 'admin-users' }
  }

  // 用户路由守卫
  if (to.meta.requiresAuth) {
    if (authStore.token && !authStore.user) {
      await authStore.loadProfile()
    }

    if (!authStore.isAuthenticated) {
      return { name: 'login', query: { redirect: to.fullPath } }
    }
  }

  if (to.meta.guestOnly && authStore.isAuthenticated) {
    return { name: 'dashboard' }
  }

  return true
})

export default router
