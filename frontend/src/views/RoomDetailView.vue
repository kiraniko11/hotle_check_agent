<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft,
  Check,
  Collection,
  InfoFilled,
  Location,
  Star,
} from '@element-plus/icons-vue'

import {
  createBooking,
  createReview,
  fetchRoomReviews,
  fetchRoomTypeDetail,
  getFavoriteStatus,
  getUserBookings,
  toggleFavorite,
} from '../api/rooms'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const roomTypeId = Number(route.params.id)
const roomType = ref(null)
const loading = ref(true)

const isFavorite = ref(false)
const favoriteLoading = ref(false)

const reviews = ref([])
const isEligibleForReview = ref(false)
const reviewForm = reactive({ rating: 5, content: '' })
const reviewLoading = ref(false)

const startDate = ref('')
const endDate = ref('')
const dialogVisible = ref(false)
const payLoading = ref(false)

const paymentForm = reactive({
  contact_name: '',
  contact_phone: '',
  id_card: '',
  payment_method: 'hang_charge',
})

const paymentChannels = [
  { key: 'wechat', label: '微信支付', className: 'wechat' },
  { key: 'alipay', label: '支付宝', className: 'alipay' },
  { key: 'hang_charge', label: '会员挂账', className: 'hang-charge' },
]

// 限制入住日期不能早于今天。
const disabledStartDate = (time) => time.getTime() < Date.now() - 8.64e7

// 限制退房日期不能早于等于入住日期。
const disabledEndDate = (time) => {
  if (!startDate.value) {
    return time.getTime() < Date.now() - 8.64e7
  }
  return time.getTime() <= new Date(startDate.value).getTime()
}

// 计算入住天数。
const stayDays = computed(() => {
  if (!startDate.value || !endDate.value) return 0
  const diffTime = Math.abs(new Date(endDate.value) - new Date(startDate.value))
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24))
})

// 计算订单预估总价。
const totalPrice = computed(() => {
  if (!roomType.value || stayDays.value <= 0) return 0
  return stayDays.value * Number(roomType.value.price)
})

// 平均评分。
const averageRating = computed(() => {
  if (reviews.value.length === 0) return 0
  const total = reviews.value.reduce((sum, item) => sum + Number(item.rating || 0), 0)
  return (total / reviews.value.length).toFixed(1)
})

// 格式化日期。
function formatDate(dateObj) {
  if (!dateObj) return ''
  const d = new Date(dateObj)
  const month = '' + (d.getMonth() + 1)
  const day = '' + d.getDate()
  const year = d.getFullYear()
  return [year, month.padStart(2, '0'), day.padStart(2, '0')].join('-')
}

function formatDateTime(value) {
  if (!value) return ''
  return String(value).substring(0, 10)
}

// 加载房型详情。
async function loadDetail() {
  const response = await fetchRoomTypeDetail(roomTypeId)
  if (response.data && response.data.code === 200) {
    roomType.value = response.data.data
  }
}

// 查询收藏状态。
async function loadFavoriteStatus() {
  try {
    const response = await getFavoriteStatus(roomTypeId)
    if (response.data && response.data.code === 200) {
      isFavorite.value = response.data.data.is_favorite
    }
  } catch {
    isFavorite.value = false
  }
}

// 加载历史评价。
async function loadReviews() {
  const response = await fetchRoomReviews(roomTypeId)
  if (response.data && response.data.code === 200) {
    reviews.value = response.data.data
  }
}

// 判断当前用户是否预订过该房型（与后端校验保持一致）。
async function checkReviewEligibility() {
  try {
    const response = await getUserBookings()
    if (response.data && response.data.code === 200) {
      const userBookings = response.data.data
      isEligibleForReview.value = userBookings.some(
        (b) => b.room_type === roomTypeId && b.status !== 'cancelled'
      )
    }
  } catch {
    isEligibleForReview.value = false
  }
}

// 切换收藏状态。
async function handleToggleFavorite() {
  favoriteLoading.value = true
  try {
    const response = await toggleFavorite(roomTypeId)
    if (response.data && response.data.code === 200) {
      isFavorite.value = response.data.data.is_favorite
      ElMessage.success(response.data.msg)
    }
  } finally {
    favoriteLoading.value = false
  }
}

// 发表评价。
async function handleSubmitReview() {
  if (!reviewForm.content.trim()) {
    ElMessage.warning('请输入评价内容')
    return
  }

  reviewLoading.value = true
  try {
    const response = await createReview(roomTypeId, {
      rating: reviewForm.rating,
      content: reviewForm.content.trim(),
    })
    if (response.data && response.data.code === 200) {
      ElMessage.success('评价发表成功')
      reviewForm.content = ''
      reviewForm.rating = 5
      await loadReviews()
    } else {
      ElMessage.error(response.data?.msg || '评价发表失败')
    }
  } finally {
    reviewLoading.value = false
  }
}

// 打开预订弹窗，优先使用用户资料预填联系人。
function openBookingDialog() {
  if (!startDate.value || !endDate.value) {
    ElMessage.warning('请先选择入住与退房日期')
    return
  }
  const profile = authStore.user || {}
  paymentForm.contact_name = `${profile.last_name || ''}${profile.first_name || ''}`.trim()
  paymentForm.contact_phone = profile.mobile || ''
  dialogVisible.value = true
}

// 确认支付并提交预订。
async function handleConfirmPaymentAndBook() {
  if (!paymentForm.contact_name.trim()) {
    ElMessage.warning('请输入入住登记人的真实姓名')
    return
  }
  const phoneReg = /^1[3-9]\d{9}$/
  if (!phoneReg.test(paymentForm.contact_phone)) {
    ElMessage.warning('请输入正确的11位联系电话')
    return
  }
  const idCardReg = /^[1-9]\d{5}(18|19|20)\d{2}((0[1-9])|(1[0-2]))(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]$/
  if (!idCardReg.test(paymentForm.id_card)) {
    ElMessage.warning('请输入合法的18位身份证号码')
    return
  }

  payLoading.value = true
  // 延迟1.5秒以模拟安全网关交易通信。
  setTimeout(async () => {
    try {
      const payload = {
        start_date: formatDate(startDate.value),
        end_date: formatDate(endDate.value),
        contact_name: paymentForm.contact_name.trim(),
        contact_phone: paymentForm.contact_phone.trim(),
        id_card: paymentForm.id_card.trim(),
        payment_method: paymentForm.payment_method,
      }
      const response = await createBooking(roomTypeId, payload)
      if (response.data && response.data.code === 200) {
        ElMessage.success('资金清算成功，客房预订已确认！')
        dialogVisible.value = false
        router.push('/profile')
      } else {
        ElMessage.error(response.data?.msg || '预订失败')
      }
    } finally {
      payLoading.value = false
    }
  }, 1500)
}

onMounted(async () => {
  loading.value = true
  await Promise.all([
    loadDetail(),
    loadFavoriteStatus(),
    checkReviewEligibility(),
    loadReviews(),
  ])
  loading.value = false
})
</script>

<template>
  <main v-loading="loading" class="detail-container">
    <div class="detail-body">
      <div class="back-nav-row">
        <el-button link class="back-link-btn" :icon="ArrowLeft" @click="router.push('/rooms')">
          返回客房列表
        </el-button>
      </div>

      <div v-if="roomType" class="detail-body-split">
        <!-- 左栏：房型介绍与物理房号 -->
        <div class="detail-left-col">
          <div class="hero-image-wrapper">
            <img class="hero-image" :src="roomType.cover_image" :alt="roomType.name" />
            <div class="hero-mask">
              <h1 class="hero-title">{{ roomType.name }}</h1>
            </div>
          </div>

          <section class="info-card">
            <div class="section-title">
              <el-icon class="title-icon"><InfoFilled /></el-icon>
              <h2>房型介绍</h2>
            </div>
            <p class="description-text">{{ roomType.description }}</p>

            <el-descriptions :column="2" border class="spec-table">
              <el-descriptions-item label="每晚价格">
                <span class="price-val-text">¥{{ Math.round(roomType.price) }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="可住人数">{{ roomType.capacity }} 人</el-descriptions-item>
              <el-descriptions-item label="建筑面积">{{ roomType.area }} ㎡</el-descriptions-item>
              <el-descriptions-item label="床型配置">{{ roomType.bed_type }}</el-descriptions-item>
              <el-descriptions-item label="窗户">
                {{ roomType.window ? '配备观景窗' : '无窗' }}
              </el-descriptions-item>
              <el-descriptions-item label="早餐">
                {{ roomType.breakfast ? '含精选早餐' : '不含早餐' }}
              </el-descriptions-item>
            </el-descriptions>
          </section>

          <section class="rooms-section">
            <div class="section-title">
              <el-icon class="title-icon"><Location /></el-icon>
              <h2>本房型实体房号</h2>
            </div>
            <div v-if="roomType.rooms && roomType.rooms.length" class="rooms-grid">
              <div v-for="room in roomType.rooms" :key="room.id" class="room-item-card">
                <div class="room-header">
                  <span class="room-num">{{ room.room_number }}</span>
                  <span class="room-floor">{{ room.floor }} 层</span>
                </div>
                <el-tag
                  class="status-badge"
                  :type="room.status === 'vacant' ? 'success' : 'info'"
                  size="small"
                >
                  {{ room.status_display }}
                </el-tag>
              </div>
            </div>
            <el-empty v-else class="empty-rooms" description="该房型暂未录入实体房号" />
          </section>
        </div>

        <!-- 右栏：常驻预订面板 -->
        <aside class="detail-right-col">
          <div class="sticky-booking-panel">
            <div class="favorite-action-bar">
              <el-button
                class="favorite-toggle-btn"
                :class="{ 'is-active': isFavorite }"
                :loading="favoriteLoading"
                @click="handleToggleFavorite"
              >
                <el-icon class="fav-heart-icon"><Collection /></el-icon>
                {{ isFavorite ? '已收藏，点击取消' : '收藏该房型' }}
              </el-button>
            </div>

            <div class="booking-card">
              <h2 class="booking-title">预订客房</h2>
              <div class="booking-subtitle">RESERVATION</div>

              <div class="booking-form">
                <label class="form-item">
                  <span class="form-label">入住日期</span>
                  <el-date-picker
                    v-model="startDate"
                    type="date"
                    value-format="YYYY-MM-DD"
                    placeholder="选择入住日期"
                    class="luxury-date-picker"
                    :disabled-date="disabledStartDate"
                  />
                </label>

                <label class="form-item">
                  <span class="form-label">退房日期</span>
                  <el-date-picker
                    v-model="endDate"
                    type="date"
                    value-format="YYYY-MM-DD"
                    placeholder="选择退房日期"
                    class="luxury-date-picker"
                    :disabled-date="disabledEndDate"
                  />
                </label>

                <div class="price-summary-box">
                  <div v-if="stayDays <= 0" class="summary-placeholder">
                    请选择入住与退房日期以查看费用明细
                  </div>
                  <div v-else class="summary-details">
                    <div class="summary-row">
                      <span>每晚房价</span>
                      <span>¥{{ Math.round(roomType.price) }}</span>
                    </div>
                    <div class="summary-row">
                      <span>入住天数</span>
                      <span>{{ stayDays }} 晚</span>
                    </div>
                    <div class="divider"></div>
                    <div class="summary-row total">
                      <span>预估总价</span>
                      <span class="total-price-val">¥{{ Math.round(totalPrice) }}</span>
                    </div>
                  </div>
                </div>

                <el-button
                  class="booking-submit-btn"
                  :disabled="roomType.remaining_stock <= 0"
                  @click="openBookingDialog"
                >
                  {{ roomType.remaining_stock > 0 ? '立即预订' : '库存不足' }}
                </el-button>
                <p class="stock-hint">
                  当前剩余可用客房 {{ roomType.remaining_stock }} 间 / 共 {{ roomType.total_stock }} 间
                </p>
              </div>
            </div>
          </div>
        </aside>
      </div>

      <!-- 底部评价展台 -->
      <section v-if="roomType" class="reviews-section-wrapper">
        <div class="section-header">
          <span class="sub-title">住客心声</span>
          <h2 class="title">真实入住评价</h2>
          <p class="desc">
            平均评分
            <strong>{{ averageRating }}</strong>
            / 5.0 · 共 {{ reviews.length }} 条评价
          </p>
        </div>

        <div class="review-posting-box">
          <div v-if="isEligibleForReview" class="review-form-card">
            <h3 class="form-title">发表您的入住体验</h3>
            <p class="form-desc">仅向真实预订过该房型的宾客开放评价。</p>
            <div class="review-form">
              <div class="form-rating-row">
                <span class="rating-label">评分</span>
                <el-rate v-model="reviewForm.rating" :max="5" />
              </div>
              <el-input
                v-model="reviewForm.content"
                type="textarea"
                :rows="3"
                maxlength="300"
                show-word-limit
                placeholder="请描述您的入住感受，例如房间设施、服务与卫生情况"
              />
              <el-button
                class="review-submit-btn"
                :loading="reviewLoading"
                @click="handleSubmitReview"
              >
                提交评价
              </el-button>
            </div>
          </div>

          <div v-else class="review-restricted-card">
            <el-icon class="lock-icon"><Star /></el-icon>
            <div class="restricted-info">
              <h4>评价资格受限</h4>
              <p>只有真实预订并体验过该客房的宾客才能发表评价，预订完成后即可回来分享感受。</p>
            </div>
          </div>
        </div>

        <div class="reviews-display-list">
          <div v-if="reviews.length" class="reviews-grid-cards">
            <article v-for="item in reviews" :key="item.id" class="review-item-card">
              <div class="review-item-header">
                <span class="reviewer-name">{{ item.username }}</span>
                <span class="review-date">{{ formatDateTime(item.created_at) }}</span>
              </div>
              <el-rate :model-value="Number(item.rating)" disabled size="small" />
              <p class="review-item-content">{{ item.content }}</p>
            </article>
          </div>
          <el-empty v-else description="还没有住客评价，期待您成为第一位分享者" />
        </div>
      </section>
    </div>

    <!-- 实名登记与支付弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      title="实名登记与在线支付"
      width="560px"
      class="luxury-pay-dialog"
      :close-on-click-modal="false"
    >
      <div class="pay-dialog-body">
        <div class="billing-summary-section">
          <h3 class="summary-title">行程简报</h3>
          <div class="summary-details">
            <div class="detail-row">
              <span class="label">房型</span>
              <span class="val">{{ roomType?.name }}</span>
            </div>
            <div class="detail-row">
              <span class="label">入住 / 退房</span>
              <span class="val">{{ startDate }} 至 {{ endDate }}</span>
            </div>
            <div class="detail-row">
              <span class="label">入住天数</span>
              <span class="val">{{ stayDays }} 晚</span>
            </div>
            <div class="detail-row total">
              <span class="label">应付总额</span>
              <span class="val price">¥{{ Math.round(totalPrice) }}</span>
            </div>
          </div>
        </div>

        <div class="real-name-section">
          <h3 class="form-section-title">入住人实名登记</h3>
          <el-form label-position="top" class="luxury-form">
            <el-form-item label="入住人姓名">
              <el-input
                v-model="paymentForm.contact_name"
                class="luxury-input"
                placeholder="请输入入住登记人的真实姓名"
              />
            </el-form-item>
            <el-form-item label="联系电话">
              <el-input
                v-model="paymentForm.contact_phone"
                class="luxury-input"
                maxlength="11"
                placeholder="请输入11位手机号"
              />
            </el-form-item>
            <el-form-item label="身份证号">
              <el-input
                v-model="paymentForm.id_card"
                class="luxury-input"
                maxlength="18"
                placeholder="请输入18位身份证号码"
              />
            </el-form-item>
          </el-form>
        </div>

        <div class="payment-channels-section">
          <h3 class="channels-title">选择支付渠道</h3>
          <div class="channels-grid">
            <div
              v-for="channel in paymentChannels"
              :key="channel.key"
              class="channel-card"
              :class="[channel.className, { 'is-selected': paymentForm.payment_method === channel.key }]"
              @click="paymentForm.payment_method = channel.key"
            >
              <span class="checked-dot"></span>
              <span class="channel-name">{{ channel.label }}</span>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer-actions">
          <el-button @click="dialogVisible = false">暂不支付</el-button>
          <el-button
            class="pay-confirm-btn"
            type="primary"
            :loading="payLoading"
            :icon="Check"
            @click="handleConfirmPaymentAndBook"
          >
            确认支付并预订
          </el-button>
        </div>
      </template>
    </el-dialog>
  </main>
</template>

<style scoped>
.detail-container {
  min-height: 100vh;
  background-color: #f4f7fb;
  padding-bottom: 80px;
}

.back-nav-row {
  margin-bottom: 12px;
}

.back-link-btn {
  color: #16324f !important;
  font-weight: 700;
  font-size: 13px;
  letter-spacing: 0.5px;
}

.back-link-btn:hover {
  color: #4f8ef7 !important;
}

.detail-body {
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px 24px 0;
}

/* 不对称左右分栏 */
.detail-body-split {
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  gap: 36px;
  align-items: start;
}

.detail-left-col {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

/* 大图巨幕 */
.hero-image-wrapper {
  position: relative;
  height: 380px;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 8px 30px rgba(22, 50, 79, 0.05);
  border: 1px solid rgba(22, 50, 79, 0.12);
}

.hero-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.hero-mask {
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(22, 50, 79, 0.75) 0%, rgba(22, 50, 79, 0.1) 100%);
  display: flex;
  align-items: flex-end;
  padding: 30px 40px;
}

.hero-title {
  color: #ffffff;
  font-size: 32px;
  font-weight: 800;
  font-family: 'Georgia', serif;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  letter-spacing: 1px;
  margin: 0;
}

/* 详情介绍卡片 */
.info-card,
.rooms-section {
  background: #ffffff;
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 10px 30px rgba(22, 50, 79, 0.02);
  border: 1px solid rgba(22, 50, 79, 0.08);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
  color: #1a2b40;
}

.title-icon {
  color: #4f8ef7;
  font-size: 20px;
}

.section-title h2 {
  font-size: 16px;
  font-weight: 800;
  margin: 0;
  letter-spacing: 0.5px;
}

.description-text {
  font-size: 14px;
  line-height: 1.7;
  color: #46566b;
  margin: 0 0 24px 0;
}

.price-val-text {
  font-size: 18px;
  font-weight: 800;
  color: #2f6fd8;
}

/* 房间物理网格 */
.rooms-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 16px;
}

.room-item-card {
  background: #ffffff;
  border: 1px solid rgba(22, 50, 79, 0.08);
  border-radius: 10px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}

.room-item-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(22, 50, 79, 0.05);
}

.room-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.room-num {
  font-size: 20px;
  font-weight: 700;
  color: #1a2b40;
}

.room-floor {
  font-size: 12px;
  color: #8494ab;
}

.room-status {
  width: 100%;
}

.status-badge {
  width: 100%;
  pointer-events: none;
}

.empty-rooms {
  padding: 20px 0;
}

/* 右侧侧边栏 - 悬浮常驻面板 */
.detail-right-col {
  position: sticky;
  top: 96px;
  z-index: 1000;
}

.sticky-booking-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 收藏按钮条 */
.favorite-action-bar {
  background: #ffffff;
  border-radius: 12px;
  padding: 14px 20px;
  border: 1px solid rgba(22, 50, 79, 0.08);
  box-shadow: 0 10px 30px rgba(22, 50, 79, 0.02);
}

.favorite-toggle-btn {
  width: 100%;
  height: 44px;
  border-color: rgba(22, 50, 79, 0.1) !important;
  background: transparent !important;
  color: #46566b !important;
  font-weight: 700;
  font-size: 13px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.favorite-toggle-btn:hover {
  border-color: #4f8ef7 !important;
  color: #4f8ef7 !important;
  background: rgba(79, 142, 247, 0.04) !important;
}

.favorite-toggle-btn.is-active {
  background: #16324f !important;
  color: #ffffff !important;
  border-color: #16324f !important;
}

.fav-heart-icon {
  font-size: 16px;
  margin-right: 6px;
}

/* 预订卡片 */
.booking-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 32px 28px;
  border: 1px solid rgba(22, 50, 79, 0.08);
  box-shadow: 0 15px 35px rgba(22, 50, 79, 0.04);
}

.booking-title {
  font-size: 20px;
  font-weight: 800;
  color: #1a2b40;
  margin: 0 0 6px 0;
  letter-spacing: 0.5px;
}

.booking-subtitle {
  font-size: 9px;
  font-weight: 700;
  color: #4f8ef7;
  letter-spacing: 1.5px;
  margin-bottom: 24px;
  text-transform: uppercase;
}

.booking-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  font-size: 11px;
  font-weight: 700;
  color: #16324f;
  text-transform: uppercase;
}

.luxury-date-picker {
  width: 100% !important;
}

/* 费用计价结算明细 */
.price-summary-box {
  background: #f8fafd;
  border-radius: 10px;
  padding: 18px;
  border: 1px solid rgba(22, 50, 79, 0.05);
  font-size: 13px;
  color: #46566b;
}

.summary-placeholder {
  text-align: center;
  color: #a0aec0;
  padding: 10px 0;
}

.summary-details {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.summary-row.total {
  font-size: 14px;
  font-weight: 800;
  color: #1a2b40;
}

.total-price-val {
  font-size: 20px;
  color: #2f6fd8;
}

.price-summary-box .divider {
  height: 1px;
  background: rgba(22, 50, 79, 0.08);
  margin: 4px 0;
}

.booking-submit-btn {
  background: #16324f !important;
  border-color: #16324f !important;
  color: #ffffff !important;
  font-weight: 700;
  height: 48px;
  border-radius: 8px;
  font-size: 14px;
  box-shadow: 0 4px 15px rgba(22, 50, 79, 0.15);
  transition: all 0.3s ease;
  margin-top: 10px;
  width: 100%;
}

.booking-submit-btn:hover {
  background: #1a2b40 !important;
  border-color: #1a2b40 !important;
}

.booking-submit-btn:disabled {
  background: #cbd5e0 !important;
  border-color: #cbd5e0 !important;
  color: #ffffff !important;
}

.stock-hint {
  font-size: 11px;
  color: #8494ab;
  text-align: center;
  font-weight: 500;
  margin: 0;
}

/* 底部评价展台 */
.reviews-section-wrapper {
  border-top: 1px solid rgba(22, 50, 79, 0.08);
  margin-top: 64px;
  padding-top: 64px;
}

.reviews-section-wrapper .section-header {
  text-align: center;
  max-width: 650px;
  margin: 0 auto 40px auto;
}

.reviews-section-wrapper .section-header .sub-title {
  font-size: 11px;
  font-weight: 700;
  color: #16324f;
  letter-spacing: 2px;
  text-transform: uppercase;
  display: block;
  margin-bottom: 8px;
}

.reviews-section-wrapper .section-header .title {
  font-size: 26px;
  font-weight: 800;
  color: #1a2b40;
  margin: 0 0 12px 0;
  font-family: 'Georgia', serif;
}

.reviews-section-wrapper .section-header .desc {
  font-size: 14px;
  line-height: 1.6;
  color: #8494ab;
  margin: 0;
}

.reviews-section-wrapper .section-header .desc strong {
  color: #2f6fd8;
  font-size: 18px;
}

/* 评论表单 */
.review-posting-box {
  margin-bottom: 48px;
}

.review-form-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 30px;
  border: 1px solid rgba(22, 50, 79, 0.08);
  box-shadow: 0 8px 30px rgba(22, 50, 79, 0.02);
}

.review-form-card .form-title {
  font-size: 16px;
  font-weight: 800;
  color: #1a2b40;
  margin: 0 0 4px 0;
}

.review-form-card .form-desc {
  font-size: 12px;
  color: #8494ab;
  margin: 0 0 20px 0;
}

.review-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
  align-items: flex-start;
}

.form-rating-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.rating-label {
  font-size: 13px;
  color: #46566b;
  font-weight: 700;
}

.review-submit-btn {
  background: #16324f !important;
  border-color: #16324f !important;
  color: #ffffff !important;
  font-weight: 700;
  padding: 10px 24px;
  border-radius: 6px;
}

.review-submit-btn:hover {
  background: #1a2b40 !important;
}

/* 限制评价提示卡片 */
.review-restricted-card {
  background: #fdfaf7;
  border-radius: 12px;
  padding: 24px;
  border: 1px dashed rgba(79, 142, 247, 0.4);
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.lock-icon {
  font-size: 24px;
  color: #4f8ef7;
  margin-top: 2px;
}

.restricted-info h4 {
  font-size: 14px;
  font-weight: 800;
  color: #1a2b40;
  margin: 0 0 4px 0;
}

.restricted-info p {
  font-size: 12px;
  color: #8494ab;
  margin: 0;
}

/* 历史评语列表 */
.reviews-display-list {
  border-top: 1px solid rgba(22, 50, 79, 0.08);
  padding-top: 40px;
}

.reviews-grid-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

.reviews-grid-cards .review-item-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid rgba(22, 50, 79, 0.08);
  box-shadow: 0 6px 20px rgba(22, 50, 79, 0.01);
  display: flex;
  flex-direction: column;
  gap: 10px;
  height: fit-content;
}

.review-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.reviewer-name {
  font-size: 13px;
  font-weight: 800;
  color: #1a2b40;
}

.review-date {
  font-size: 11px;
  color: #cbd5e0;
}

.review-item-content {
  font-size: 13px;
  line-height: 1.6;
  color: #46566b;
  margin: 0;
  text-align: justify;
}

@media (max-width: 992px) {
  .detail-body-split {
    grid-template-columns: 1fr;
  }

  .detail-right-col {
    position: static;
  }

  .reviews-grid-cards {
    grid-template-columns: 1fr;
  }
}

/* 预订登记与支付弹窗自定义样式 */
.pay-dialog-body {
  padding: 10px 0;
  display: flex;
  flex-direction: column;
  gap: 24px;
  max-height: 60vh;
  overflow-y: auto;
}

/* 行程简报 */
.billing-summary-section {
  background: rgba(22, 50, 79, 0.03);
  border: 1px solid rgba(22, 50, 79, 0.08);
  border-radius: 8px;
  padding: 16px 20px;
}

.summary-title,
.form-section-title,
.channels-title {
  font-size: 13px;
  font-weight: 800;
  color: #1a2b40;
  margin: 0 0 12px 0;
  border-left: 3px solid #4f8ef7;
  padding-left: 10px;
}

.billing-summary-section .summary-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #46566b;
}

.detail-row .label {
  color: #8494ab;
  font-weight: 600;
}

.detail-row .val {
  font-weight: 700;
}

.detail-row.total {
  margin-top: 6px;
  border-top: 1px dashed rgba(22, 50, 79, 0.15);
  padding-top: 8px;
}

.detail-row.total .val.price {
  color: #2f6fd8;
  font-size: 16px;
  font-weight: 800;
}

/* 支付渠道 */
.channels-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.channel-card {
  border: 1px solid rgba(22, 50, 79, 0.1);
  border-radius: 10px;
  padding: 16px 12px;
  text-align: center;
  cursor: pointer;
  position: relative;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  background: #ffffff;
}

.channel-card .checked-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 1.5px solid rgba(22, 50, 79, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.channel-card .checked-dot::after {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: transparent;
  transition: all 0.2s ease;
}

.channel-card .channel-name {
  font-size: 12px;
  font-weight: 700;
  color: #46566b;
}

.channel-card.wechat.is-selected {
  border-color: #27ae60;
  background: rgba(39, 174, 96, 0.03);
}

.channel-card.wechat.is-selected .checked-dot {
  border-color: #27ae60;
  background: #27ae60;
}

.channel-card.wechat.is-selected .checked-dot::after {
  background: #ffffff;
}

.channel-card.wechat.is-selected .channel-name {
  color: #27ae60;
}

.channel-card.alipay.is-selected {
  border-color: #2980b9;
  background: rgba(41, 128, 185, 0.03);
}

.channel-card.alipay.is-selected .checked-dot {
  border-color: #2980b9;
  background: #2980b9;
}

.channel-card.alipay.is-selected .checked-dot::after {
  background: #ffffff;
}

.channel-card.alipay.is-selected .channel-name {
  color: #2980b9;
}

.channel-card.hang-charge.is-selected {
  border-color: #4f8ef7;
  background: rgba(79, 142, 247, 0.06);
}

.channel-card.hang-charge.is-selected .checked-dot {
  border-color: #4f8ef7;
  background: #4f8ef7;
}

.channel-card.hang-charge.is-selected .checked-dot::after {
  background: #ffffff;
}

.channel-card.hang-charge.is-selected .channel-name {
  color: #16324f;
}

/* 弹窗操作栏 */
.dialog-footer-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.pay-confirm-btn {
  background: #16324f !important;
  border-color: #16324f !important;
  font-weight: 700;
  flex: 1;
}

.pay-confirm-btn:hover {
  background: #1a2b40 !important;
}
</style>
