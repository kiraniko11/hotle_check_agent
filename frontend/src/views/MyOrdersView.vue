<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowRight, CircleClose, Tickets } from '@element-plus/icons-vue'

import { cancelBooking, getUserBookings } from '../api/rooms'

const router = useRouter()
const bookings = ref([])
const loading = ref(true)
const activeStatus = ref('')

// 各状态的订单数量统计。
const stats = computed(() => ({
  total: bookings.value.length,
  booked: bookings.value.filter(b => b.status === 'booked').length,
  checked_in: bookings.value.filter(b => b.status === 'checked_in').length,
  completed: bookings.value.filter(b => b.status === 'completed').length,
  cancelled: bookings.value.filter(b => b.status === 'cancelled').length,
}))

const statCards = computed(() => [
  { key: '', label: '全部订单', value: stats.value.total },
  { key: 'booked', label: '已预订', value: stats.value.booked },
  { key: 'checked_in', label: '已入住', value: stats.value.checked_in },
  { key: 'completed', label: '已完成', value: stats.value.completed },
  { key: 'cancelled', label: '已取消', value: stats.value.cancelled },
])

// 按状态过滤展示的订单列表。
const filteredBookings = computed(() => {
  if (!activeStatus.value) return bookings.value
  return bookings.value.filter(b => b.status === activeStatus.value)
})

// 身份证脱敏。
function maskIdCard(str) {
  if (!str || str.length !== 18) return str || '未登记'
  return str.substring(0, 6) + '********' + str.substring(14)
}

function statusTagType(status) {
  if (status === 'booked') return 'primary'
  if (status === 'checked_in') return 'warning'
  if (status === 'completed') return 'success'
  return 'info'
}

function paymentLabel(method) {
  const mapping = { wechat: '微信支付', alipay: '支付宝', hang_charge: '会员挂账' }
  return mapping[method] || method || '会员挂账'
}

// 加载订单列表。
async function loadBookings() {
  loading.value = true
  try {
    const response = await getUserBookings()
    if (response.data && response.data.code === 200) {
      bookings.value = response.data.data
    }
  } finally {
    loading.value = false
  }
}

// 取消预订行程，成功后刷新列表。
function handleCancelBooking(booking) {
  ElMessageBox.confirm(
    `确定要取消 "${booking.room_type_name}" 的预订行程（单号 ${booking.id}）吗？取消后房源将立即释放。`,
    '取消行程确认',
    { confirmButtonText: '确定取消', cancelButtonText: '保留行程', type: 'warning' }
  ).then(async () => {
    const response = await cancelBooking(booking.id)
    if (response.data && response.data.code === 200) {
      ElMessage.success(response.data.msg || '预订已取消，房源库存已恢复。')
      await loadBookings()
    } else {
      ElMessage.error(response.data?.msg || '取消失败')
    }
  }).catch(() => {})
}

onMounted(() => {
  loadBookings()
})
</script>

<template>
  <main class="orders-page">
    <div class="orders-body">
      <header class="page-head">
        <span class="eyebrow">MY RESERVATIONS</span>
        <h1>我的订单</h1>
        <p>查看全部预订行程，管理入住信息并在需要时释放房源。</p>
      </header>

      <section class="stat-strip">
        <button
          v-for="card in statCards"
          :key="card.key"
          type="button"
          class="stat-card"
          :class="{ active: activeStatus === card.key }"
          @click="activeStatus = activeStatus === card.key ? '' : card.key"
        >
          <span class="stat-label">{{ card.label }}</span>
          <strong class="stat-value">{{ card.value }}</strong>
        </button>
      </section>

      <section v-loading="loading" class="orders-list">
        <el-empty v-if="!loading && filteredBookings.length === 0" description="暂无订单记录">
          <el-button class="book-now-btn" @click="router.push('/rooms')">去挑选心仪客房</el-button>
        </el-empty>

        <article v-for="b in filteredBookings" :key="b.id" class="order-card">
          <div class="order-main">
            <div class="order-head">
              <div class="order-title-group">
                <el-icon class="order-icon"><Tickets /></el-icon>
                <h3>{{ b.room_type_name }}</h3>
              </div>
              <el-tag :type="statusTagType(b.status)" size="small" effect="light">
                {{ b.status_display }}
              </el-tag>
            </div>

            <div class="order-meta">
              <div class="meta-item">
                <span class="meta-label">订单号</span>
                <span class="meta-value">#{{ b.id }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">分配房号</span>
                <span class="meta-value">{{ b.room_number || '待分配' }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">入住日期</span>
                <span class="meta-value">{{ b.start_date }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">退房日期</span>
                <span class="meta-value">{{ b.end_date }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">入住人</span>
                <span class="meta-value">{{ b.contact_name || '未登记' }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">联系电话</span>
                <span class="meta-value">{{ b.contact_phone || '未登记' }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">身份证号</span>
                <span class="meta-value">{{ maskIdCard(b.id_card) }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">支付方式</span>
                <span class="meta-value">{{ paymentLabel(b.payment_method) }}</span>
              </div>
            </div>
          </div>

          <div class="order-side">
            <div class="order-amount">
              <span class="amount-label">订单总额</span>
              <span class="amount-value">¥{{ Math.round(b.total_price) }}</span>
            </div>
            <div class="order-actions">
              <button
                v-if="b.status === 'booked'"
                class="cancel-order-btn"
                type="button"
                @click="handleCancelBooking(b)"
              >
                <el-icon><CircleClose /></el-icon>
                取消行程
              </button>
              <button class="view-room-btn" type="button" @click="router.push(`/rooms/${b.room_type}`)">
                查看房型
                <el-icon><ArrowRight /></el-icon>
              </button>
            </div>
          </div>
        </article>
      </section>
    </div>
  </main>
</template>

<style scoped>
.orders-page {
  min-height: 100vh;
  background-color: #f4f7fb;
  padding-bottom: 80px;
}

.orders-body {
  max-width: 1100px;
  margin: 0 auto;
  padding: 48px 24px 0;
}

.page-head {
  text-align: center;
  margin-bottom: 36px;
}

.eyebrow {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 3px;
  color: #4f8ef7;
  text-transform: uppercase;
}

.page-head h1 {
  font-size: 30px;
  font-weight: 800;
  color: #1a2b40;
  margin: 10px 0 10px;
  font-family: 'Georgia', serif;
}

.page-head p {
  font-size: 14px;
  color: #8494ab;
  margin: 0;
}

/* 统计卡片条 */
.stat-strip {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 14px;
  margin-bottom: 32px;
}

.stat-card {
  background: #ffffff;
  border: 1px solid rgba(22, 50, 79, 0.08);
  border-radius: 14px;
  padding: 18px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  cursor: pointer;
  transition: all 0.25s ease;
  font-family: inherit;
  text-align: left;
}

.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 24px rgba(22, 50, 79, 0.07);
}

.stat-card.active {
  background: #16324f;
  border-color: #16324f;
}

.stat-label {
  font-size: 12px;
  font-weight: 700;
  color: #8494ab;
  letter-spacing: 0.4px;
}

.stat-card.active .stat-label {
  color: rgba(255, 255, 255, 0.72);
}

.stat-value {
  font-size: 26px;
  font-weight: 800;
  color: #16324f;
  font-family: 'Georgia', serif;
}

.stat-card.active .stat-value {
  color: #ffffff;
}

/* 订单卡片 */
.orders-list {
  display: flex;
  flex-direction: column;
  gap: 22px;
  min-height: 200px;
}

.order-card {
  background: #ffffff;
  border: 1px solid rgba(22, 50, 79, 0.08);
  border-radius: 16px;
  padding: 26px 28px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 200px;
  gap: 24px;
  box-shadow: 0 8px 26px rgba(22, 50, 79, 0.03);
  transition: box-shadow 0.3s ease, transform 0.3s ease;
}

.order-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 14px 34px rgba(79, 142, 247, 0.14);
}

.order-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
}

.order-title-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.order-icon {
  color: #4f8ef7;
  font-size: 18px;
}

.order-head h3 {
  font-size: 19px;
  font-weight: 800;
  color: #1a2b40;
  margin: 0;
  font-family: 'Georgia', serif;
}

.order-meta {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px 18px;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.meta-label {
  font-size: 10px;
  font-weight: 700;
  color: #c3cddb;
  letter-spacing: 0.6px;
  text-transform: uppercase;
}

.meta-value {
  font-size: 13px;
  font-weight: 700;
  color: #35423b;
  word-break: break-all;
}

.order-side {
  border-left: 1px dashed rgba(22, 50, 79, 0.12);
  padding-left: 24px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 18px;
}

.amount-label {
  display: block;
  font-size: 11px;
  font-weight: 700;
  color: #c3cddb;
  letter-spacing: 0.6px;
  margin-bottom: 6px;
}

.amount-value {
  font-size: 24px;
  font-weight: 800;
  color: #2f6fd8;
  font-family: 'Georgia', serif;
}

.order-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.cancel-order-btn,
.view-room-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 38px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.25s ease;
}

.cancel-order-btn {
  background: transparent;
  border: 1px solid rgba(231, 76, 60, 0.28);
  color: #e74c3c;
}

.cancel-order-btn:hover {
  background: #e74c3c;
  color: #ffffff;
  border-color: #e74c3c;
}

.view-room-btn {
  background: #16324f;
  border: 1px solid #16324f;
  color: #ffffff;
}

.view-room-btn:hover {
  background: #1a2b40;
}

.book-now-btn {
  background: #16324f !important;
  border-color: #16324f !important;
  color: #ffffff !important;
  font-weight: 700;
}

@media (max-width: 992px) {
  .stat-strip {
    grid-template-columns: repeat(2, 1fr);
  }

  .order-card {
    grid-template-columns: 1fr;
  }

  .order-meta {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .order-side {
    border-left: none;
    border-top: 1px dashed rgba(22, 50, 79, 0.12);
    padding-left: 0;
    padding-top: 18px;
  }
}
</style>
