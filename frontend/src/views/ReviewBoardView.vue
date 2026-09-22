<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { ChatLineRound, Promotion, Star } from '@element-plus/icons-vue'

import { useAuthStore } from '../stores/auth'
import { createBoardReview, fetchReviewBoard } from '../api/rooms'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

const loading = ref(true)
const submitting = ref(false)
const summary = ref({ average: 0, total: 0, distribution: {} })
const reviews = ref([])
const roomTypes = ref([])

const reviewFormRef = ref()
const reviewForm = reactive({
  room_type: null,
  rating: 5,
  content: '',
})

const reviewRules = {
  room_type: [{ required: true, message: '请选择要评价的房型', trigger: 'change' }],
  content: [
    { required: true, message: '请填写评价内容', trigger: 'blur' },
    { min: 5, message: '评价内容至少 5 个字', trigger: 'blur' },
    { max: 500, message: '评价内容不能超过 500 字', trigger: 'blur' },
  ],
}

const isLoggedIn = computed(() => Boolean(authStore.token))

// 星级分布条的最大值，用于计算百分比宽度。
const maxDistribution = computed(() =>
  Math.max(1, ...Object.values(summary.value.distribution || {})),
)

function formatDateTime(value) {
  if (!value) return ''
  return String(value).substring(0, 10)
}

function roomTypeName(id) {
  const found = roomTypes.value.find((item) => item.id === id)
  return found ? found.name : `房型 ${id}`
}

async function loadBoard() {
  loading.value = true
  try {
    const response = await fetchReviewBoard()
    if (response.data && response.data.code === 200) {
      summary.value = response.data.data.summary
      reviews.value = response.data.data.reviews
      roomTypes.value = response.data.data.room_types
    }
  } finally {
    loading.value = false
  }
}

async function handleSubmitReview() {
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录后再发表评价')
    router.push('/login')
    return
  }

  const valid = await reviewFormRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const response = await createBoardReview({
      room_type: reviewForm.room_type,
      rating: reviewForm.rating,
      content: reviewForm.content,
    })
    if (response.data && response.data.code === 200) {
      ElMessage.success('评价发表成功，感谢你的反馈！')
      reviewForm.room_type = null
      reviewForm.rating = 5
      reviewForm.content = ''
      reviewFormRef.value.clearValidate()
      await loadBoard()
    } else {
      ElMessage.error(response.data?.msg || '评价发表失败')
    }
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadBoard()
})
</script>

<template>
  <main class="review-page">
    <!-- 评论区横幅 -->
    <section class="review-hero">
      <div class="review-hero-mask"></div>
      <div class="review-hero-content">
        <span class="eyebrow">GUEST REVIEWS</span>
        <h1>酒店点评</h1>
        <p>住过的都说真话。这里汇集了住客对每个房型的真实评价，也欢迎你留下自己的入住感受。</p>
      </div>
    </section>

    <div class="review-body">
      <!-- 评分汇总 -->
      <section class="summary-card">
        <div class="summary-score">
          <strong>{{ summary.average || '0.0' }}</strong>
          <div class="score-meta">
            <el-rate :model-value="Number(summary.average)" disabled allow-half />
            <span>共 {{ summary.total }} 条评价</span>
          </div>
        </div>

        <div class="summary-bars">
          <div v-for="star in [5, 4, 3, 2, 1]" :key="star" class="bar-row">
            <span class="bar-label">{{ star }} 星</span>
            <div class="bar-track">
              <div
                class="bar-fill"
                :style="{
                  width: `${Math.round(((summary.distribution?.[star] || 0) / maxDistribution) * 100)}%`,
                }"
              ></div>
            </div>
            <span class="bar-count">{{ summary.distribution?.[star] || 0 }}</span>
          </div>
        </div>
      </section>

      <div class="review-layout">
        <!-- 发表评价 -->
        <section class="form-card">
          <h3 class="card-title">
            <el-icon><Promotion /></el-icon>
            发表我的评价
          </h3>

          <template v-if="isLoggedIn">
            <el-form
              ref="reviewFormRef"
              :model="reviewForm"
              :rules="reviewRules"
              label-position="top"
              class="review-form"
            >
              <el-form-item label="选择房型" prop="room_type">
                <el-select
                  v-model="reviewForm.room_type"
                  placeholder="你住过的房型"
                  style="width: 100%"
                >
                  <el-option
                    v-for="item in roomTypes"
                    :key="item.id"
                    :label="item.name"
                    :value="item.id"
                  />
                </el-select>
              </el-form-item>

              <el-form-item label="入住评分">
                <el-rate v-model="reviewForm.rating" show-score score-template="{value} 分" />
              </el-form-item>

              <el-form-item label="评价内容" prop="content">
                <el-input
                  v-model="reviewForm.content"
                  type="textarea"
                  :rows="5"
                  maxlength="500"
                  show-word-limit
                  placeholder="房间干不干净、睡得踏不踏实、服务怎么样……说说你的真实感受"
                />
              </el-form-item>

              <el-button
                class="submit-btn"
                type="primary"
                :loading="submitting"
                @click="handleSubmitReview"
              >
                发表评价
              </el-button>
            </el-form>
          </template>

          <div v-else class="login-tip">
            <p>登录之后就可以发表评价啦</p>
            <el-button type="primary" @click="router.push('/login')">去登录</el-button>
          </div>
        </section>

        <!-- 评论列表 -->
        <section v-loading="loading" class="list-card">
          <h3 class="card-title">
            <el-icon><ChatLineRound /></el-icon>
            全部评价（{{ reviews.length }}）
          </h3>

          <el-empty v-if="!loading && reviews.length === 0" description="还没有评价，来抢沙发" />

          <div v-else class="review-list">
            <article v-for="item in reviews" :key="item.id" class="review-item">
              <div class="review-head">
                <div class="review-user">
                  <el-avatar :size="34" :src="item.avatar || undefined">
                    {{ (item.username || '客').slice(0, 1).toUpperCase() }}
                  </el-avatar>
                  <div class="user-meta">
                    <strong>{{ item.username }}</strong>
                    <el-tag size="small" effect="plain">{{ roomTypeName(item.room_type) }}</el-tag>
                  </div>
                </div>
                <div class="review-stars">
                  <el-rate :model-value="item.rating" disabled />
                  <span class="review-time">{{ formatDateTime(item.created_at) }}</span>
                </div>
              </div>
              <p class="review-content">{{ item.content }}</p>
            </article>
          </div>
        </section>
      </div>
    </div>
  </main>
</template>

<style scoped>
.review-page {
  min-height: 100vh;
  background-color: #f4f7fb;
  padding-bottom: 80px;
}

/* 横幅 */
.review-hero {
  height: 280px;
  position: relative;
  background-image: url('../assets/photo-1566665797739-1674de7a421a.avif');
  background-size: cover;
  background-position: center;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.review-hero-mask {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(22, 50, 79, 0.6) 0%, rgba(244, 247, 251, 0.94) 88%, #f4f7fb 100%);
}

.review-hero-content {
  position: relative;
  z-index: 2;
  max-width: 720px;
  padding: 0 24px;
}

.eyebrow {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 3px;
  color: #16324f;
  text-transform: uppercase;
}

.review-hero-content h1 {
  font-size: 32px;
  font-weight: 800;
  color: #16324f;
  margin: 10px 0;
}

.review-hero-content p {
  font-size: 14px;
  line-height: 1.8;
  color: #46566b;
  margin: 0;
}

.review-body {
  max-width: 1100px;
  margin: 0 auto;
  padding: 36px 24px 0;
}

/* 评分汇总 */
.summary-card {
  display: flex;
  align-items: center;
  gap: 48px;
  background: #ffffff;
  border: 1px solid rgba(22, 50, 79, 0.08);
  border-radius: 16px;
  padding: 28px 32px;
  margin-bottom: 28px;
  box-shadow: 0 8px 24px rgba(22, 50, 79, 0.03);
}

.summary-score strong {
  font-size: 52px;
  font-weight: 800;
  color: #16324f;
  line-height: 1;
}

.score-meta {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.score-meta span {
  font-size: 12px;
  color: #8494ab;
  font-weight: 600;
}

.summary-bars {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.bar-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.bar-label {
  width: 34px;
  font-size: 12px;
  color: #8494ab;
  font-weight: 700;
}

.bar-track {
  flex: 1;
  height: 8px;
  border-radius: 4px;
  background: #eaf1fa;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 4px;
  background: #4f8ef7;
  transition: width 0.4s ease;
}

.bar-count {
  width: 24px;
  text-align: right;
  font-size: 12px;
  color: #8494ab;
  font-weight: 700;
}

/* 双栏布局 */
.review-layout {
  display: grid;
  grid-template-columns: 0.9fr 1.1fr;
  gap: 28px;
  align-items: start;
}

.form-card,
.list-card {
  background: #ffffff;
  border: 1px solid rgba(22, 50, 79, 0.08);
  border-radius: 16px;
  padding: 26px 28px;
  box-shadow: 0 10px 30px rgba(22, 50, 79, 0.03);
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 800;
  color: #1a2b40;
  margin: 0 0 20px;
}

.card-title .el-icon {
  color: #4f8ef7;
}

.review-form {
  display: flex;
  flex-direction: column;
}

.submit-btn {
  width: 100%;
  height: 44px;
  font-weight: 700;
  border-radius: 8px;
  margin-top: 4px;
}

.login-tip {
  text-align: center;
  padding: 28px 0 12px;
}

.login-tip p {
  font-size: 14px;
  color: #46566b;
  margin: 0 0 16px;
}

/* 评论列表 */
.review-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-height: 640px;
  overflow-y: auto;
  padding-right: 4px;
}

.review-item {
  border: 1px solid rgba(22, 50, 79, 0.08);
  border-radius: 12px;
  padding: 18px 20px;
  background: #fbfdff;
}

.review-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 10px;
}

.review-user {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-meta strong {
  font-size: 14px;
  color: #1a2b40;
}

.review-stars {
  display: flex;
  align-items: center;
  gap: 10px;
}

.review-time {
  font-size: 12px;
  color: #9fadc0;
  font-weight: 600;
}

.review-content {
  font-size: 13px;
  line-height: 1.7;
  color: #46566b;
  margin: 0;
  white-space: pre-wrap;
}

@media (max-width: 992px) {
  .summary-card {
    flex-direction: column;
    align-items: stretch;
    gap: 24px;
  }

  .review-layout {
    grid-template-columns: 1fr;
  }
}
</style>
