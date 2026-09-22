<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, OfficeBuilding } from '@element-plus/icons-vue'

import { fetchRoomTypes } from '../api/rooms'

const router = useRouter()
const roomTypes = ref([])
const loading = ref(true)

const filterForm = reactive({
  capacity: '',
  window: '',
  breakfast: '',
  priceRange: '',
})

// 加载符合筛选条件的房型数据。
async function loadRoomTypes() {
  loading.value = true
  try {
    const params = {}
    if (filterForm.capacity) params.capacity = filterForm.capacity
    if (filterForm.window === 'true' || filterForm.window === 'false') {
      params.window = filterForm.window
    }
    if (filterForm.breakfast === 'true' || filterForm.breakfast === 'false') {
      params.breakfast = filterForm.breakfast
    }

    const response = await fetchRoomTypes(params)
    if (response.data && response.data.code === 200) {
      let data = response.data.data
      // 按价格区间进行前端过滤。
      if (filterForm.priceRange === '300') {
        data = data.filter(item => Number(item.price) <= 300)
      } else if (filterForm.priceRange === '600') {
        data = data.filter(item => Number(item.price) > 300 && Number(item.price) <= 600)
      } else if (filterForm.priceRange === '1000') {
        data = data.filter(item => Number(item.price) > 600 && Number(item.price) <= 1000)
      } else if (filterForm.priceRange === '1000+') {
        data = data.filter(item => Number(item.price) > 1000)
      }
      roomTypes.value = data
    }
  } finally {
    loading.value = false
  }
}

// 切换芯片筛选项并立即触发检索。
function toggleChip(field, value) {
  filterForm[field] = filterForm[field] === value ? '' : value
  loadRoomTypes()
}

// 重置全部筛选条件。
function resetFilters() {
  filterForm.capacity = ''
  filterForm.window = ''
  filterForm.breakfast = ''
  filterForm.priceRange = ''
  loadRoomTypes()
}

function goDetail(id) {
  router.push(`/rooms/${id}`)
}

onMounted(() => {
  loadRoomTypes()
})
</script>

<template>
  <main class="rooms-page-container">
    <!-- 页面横幅 -->
    <section class="rooms-hero-bar">
      <div class="hero-mask"></div>
      <div class="hero-content">
        <span class="eyebrow">ROOMS</span>
        <h1 class="title">客房预订</h1>
        <p class="desc">从 98 元的单人间到家庭套房，按人数和预算筛选，价格透明没有隐藏消费。</p>
      </div>
    </section>

    <div class="rooms-page-body">
      <!-- 智能芯片筛选面板 -->
      <div class="filter-panel-wrapper">
        <div class="filter-panel">
          <div class="filter-panel-header">
            <div class="filter-title-group">
              <span class="filter-star">✦</span>
              <span class="filter-title">智能筛选</span>
              <span class="filter-subtitle">点击芯片即可即时检索</span>
            </div>
            <button class="reset-chip-btn" type="button" @click="resetFilters">重置条件</button>
          </div>

          <div class="filter-rows">
            <div class="filter-row">
              <span class="filter-row-label">入住人数</span>
              <div class="chips-wrap">
                <button
                  class="filter-chip"
                  :class="{ active: filterForm.capacity === '1' }"
                  type="button"
                  @click="toggleChip('capacity', '1')"
                >1 人</button>
                <button
                  class="filter-chip"
                  :class="{ active: filterForm.capacity === '2' }"
                  type="button"
                  @click="toggleChip('capacity', '2')"
                >2 人</button>
                <button
                  class="filter-chip"
                  :class="{ active: filterForm.capacity === '3' }"
                  type="button"
                  @click="toggleChip('capacity', '3')"
                >3 人及以上</button>
              </div>
            </div>

            <div class="filter-row">
              <span class="filter-row-label">窗户</span>
              <div class="chips-wrap">
                <button
                  class="filter-chip"
                  :class="{ active: filterForm.window === 'true' }"
                  type="button"
                  @click="toggleChip('window', 'true')"
                >必须有窗</button>
                <button
                  class="filter-chip"
                  :class="{ active: filterForm.window === 'false' }"
                  type="button"
                  @click="toggleChip('window', 'false')"
                >无窗亦可</button>
              </div>
            </div>

            <div class="filter-row">
              <span class="filter-row-label">早餐</span>
              <div class="chips-wrap">
                <button
                  class="filter-chip"
                  :class="{ active: filterForm.breakfast === 'true' }"
                  type="button"
                  @click="toggleChip('breakfast', 'true')"
                >含双早</button>
                <button
                  class="filter-chip"
                  :class="{ active: filterForm.breakfast === 'false' }"
                  type="button"
                  @click="toggleChip('breakfast', 'false')"
                >无需早餐</button>
              </div>
            </div>

            <div class="filter-row">
              <span class="filter-row-label">价格区间</span>
              <div class="chips-wrap">
                <button
                  class="filter-chip price-chip"
                  :class="{ active: filterForm.priceRange === '300' }"
                  type="button"
                  @click="toggleChip('priceRange', '300')"
                >¥300 以内</button>
                <button
                  class="filter-chip price-chip"
                  :class="{ active: filterForm.priceRange === '600' }"
                  type="button"
                  @click="toggleChip('priceRange', '600')"
                >¥300 - 600</button>
                <button
                  class="filter-chip price-chip"
                  :class="{ active: filterForm.priceRange === '1000' }"
                  type="button"
                  @click="toggleChip('priceRange', '1000')"
                >¥600 - 1000</button>
                <button
                  class="filter-chip price-chip"
                  :class="{ active: filterForm.priceRange === '1000+' }"
                  type="button"
                  @click="toggleChip('priceRange', '1000+')"
                >¥1000 以上</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 房型列表 -->
      <section v-loading="loading" class="rooms-gallery-section">
        <el-empty v-if="!loading && roomTypes.length === 0" description="没有符合条件的房型，试试放宽筛选条件">
          <el-button class="go-detail-btn" @click="resetFilters">重置筛选条件</el-button>
        </el-empty>

        <div v-else class="gallery-asymmetric-list">
          <article
            v-for="(item, index) in roomTypes"
            :key="item.id"
            class="asymmetric-room-card"
            :class="{ 'row-reverse': index % 2 !== 0 }"
          >
            <div class="card-image-box">
              <img :src="item.cover_image" :alt="item.name" />
              <div class="room-price-tag">
                <span class="curr">¥</span>
                <span class="val">{{ Math.round(item.price) }}</span>
                <span class="unit">/ 晚</span>
              </div>
            </div>

            <div class="card-info-box">
              <div class="card-info-header">
                <h3 class="room-name">{{ item.name }}</h3>
                <span class="stock-indicator" :class="{ 'low-stock': item.remaining_stock <= 2 }">
                  仅余 {{ item.remaining_stock }} 间
                </span>
              </div>

              <p class="room-intro">{{ item.description }}</p>

              <div class="spec-tags">
                <div class="spec-tag-item">
                  <span class="spec-label">面积</span>
                  <span class="spec-val">{{ item.area }} ㎡</span>
                </div>
                <div class="spec-tag-item">
                  <span class="spec-label">床型</span>
                  <span class="spec-val">{{ item.bed_type }}</span>
                </div>
                <div class="spec-tag-item">
                  <span class="spec-label">可住</span>
                  <span class="spec-val">{{ item.capacity }} 人</span>
                </div>
              </div>

              <div class="facility-badges">
                <span class="badge" :class="item.window ? 'active' : 'inactive'">
                  {{ item.window ? '有窗' : '无窗' }}
                </span>
                <span class="badge" :class="item.breakfast ? 'active' : 'inactive'">
                  {{ item.breakfast ? '含早餐' : '不含早' }}
                </span>
                <span class="badge active">独立卫浴</span>
                <span class="badge active">高速 WiFi</span>
              </div>

              <el-button class="go-detail-btn" @click="goDetail(item.id)">
                查看详情并预订
                <el-icon class="btn-icon"><ArrowRight /></el-icon>
              </el-button>
            </div>
          </article>
        </div>
      </section>
    </div>
  </main>
</template>

<style scoped>
.rooms-page-container {
  min-height: 100vh;
  background-color: #f4f7fb;
  padding-bottom: 80px;
}

/* 横通副横幅 */
.rooms-hero-bar {
  height: 280px;
  position: relative;
  background-image: url('../assets/photo-1566665797739-1674de7a421a.avif');
  background-size: cover;
  background-position: center;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: #ffffff;
}

.hero-mask {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(22, 50, 79, 0.55) 0%, rgba(244, 247, 251, 0.95) 90%, #f4f7fb 100%);
  z-index: 1;
}

.hero-content {
  position: relative;
  z-index: 2;
  max-width: 800px;
}

.eyebrow {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 3px;
  color: #16324f;
  text-transform: uppercase;
  display: block;
  margin-bottom: 12px;
}

.title {
  font-size: 32px;
  font-weight: 800;
  color: #16324f;
  margin: 0 0 12px 0;
  letter-spacing: 1px;
}

.desc {
  font-size: 14px;
  color: #46566b;
  margin: 0;
}

/* 主体内容 */
.rooms-page-body {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 24px;
}

/* 智能芯片筛选面板 */
.filter-panel-wrapper {
  margin-top: -30px;
  position: relative;
  z-index: 100;
  margin-bottom: 48px;
}

.filter-panel {
  background: #ffffff;
  border-radius: 20px;
  padding: 28px 40px 32px;
  box-shadow: 0 20px 60px rgba(22, 50, 79, 0.07), 0 4px 16px rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(22, 50, 79, 0.09);
}

.filter-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 22px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(22, 50, 79, 0.06);
}

.filter-title-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.filter-star {
  font-size: 13px;
  color: #4f8ef7;
}

.filter-title {
  font-size: 15px;
  font-weight: 800;
  color: #16324f;
  letter-spacing: 0.5px;
}

.filter-subtitle {
  font-size: 12px;
  color: #9fadc0;
  margin-left: 4px;
}

.reset-chip-btn {
  background: none;
  border: 1.5px solid rgba(22, 50, 79, 0.18);
  color: #6b7f99;
  font-size: 12px;
  font-weight: 600;
  padding: 6px 18px;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.2s ease;
  letter-spacing: 0.3px;
  font-family: inherit;
}

.reset-chip-btn:hover {
  background: #16324f;
  color: #ffffff;
  border-color: #16324f;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(22, 50, 79, 0.2);
}

.filter-rows {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 20px;
  min-height: 36px;
}

.filter-row-label {
  width: 60px;
  flex-shrink: 0;
  font-size: 11px;
  font-weight: 700;
  color: #9fadc0;
  letter-spacing: 0.8px;
  text-align: right;
}

.chips-wrap {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.filter-chip {
  background: #edf2f8;
  border: 1.5px solid transparent;
  color: #46566b;
  font-size: 13px;
  font-weight: 500;
  padding: 6px 18px;
  border-radius: 30px;
  cursor: pointer;
  transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
  letter-spacing: 0.2px;
  font-family: inherit;
  line-height: 1.4;
  user-select: none;
}

.filter-chip:hover {
  background: #e6ede7;
  color: #16324f;
  border-color: rgba(22, 50, 79, 0.14);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(22, 50, 79, 0.08);
}

.filter-chip.active {
  background: #16324f;
  color: #ffffff;
  border-color: #16324f;
  box-shadow: 0 4px 14px rgba(22, 50, 79, 0.28);
  transform: translateY(-1px);
  font-weight: 700;
}

.filter-chip.price-chip {
  font-variant-numeric: tabular-nums;
  font-size: 12.5px;
}

/* 列表展示区 */
.rooms-gallery-section {
  margin-bottom: 64px;
  min-height: 240px;
}

.gallery-asymmetric-list {
  display: flex;
  flex-direction: column;
  gap: 40px;
}

.asymmetric-room-card {
  background: #ffffff;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.02);
  border: 1px solid rgba(22, 50, 79, 0.1);
  display: flex;
  height: 320px;
  transition: transform 0.4s cubic-bezier(0.165, 0.84, 0.44, 1), box-shadow 0.4s ease;
}

.asymmetric-room-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 15px 35px rgba(79, 142, 247, 0.12);
}

.asymmetric-room-card.row-reverse {
  flex-direction: row-reverse;
}

.card-image-box {
  width: 45%;
  height: 100%;
  position: relative;
  overflow: hidden;
}

.card-image-box img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.6s ease;
}

.asymmetric-room-card:hover .card-image-box img {
  transform: scale(1.04);
}

.room-price-tag {
  position: absolute;
  top: 20px;
  left: 20px;
  background: rgba(22, 50, 79, 0.9);
  backdrop-filter: blur(6px);
  padding: 6px 14px;
  border-radius: 30px;
  color: #ffffff;
  display: flex;
  align-items: baseline;
  gap: 3px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
}

.room-price-tag .curr {
  font-size: 11px;
  color: #4f8ef7;
}

.room-price-tag .val {
  font-size: 20px;
  font-weight: 700;
  color: #f4f7fb;
}

.room-price-tag .unit {
  font-size: 10px;
  opacity: 0.7;
}

.card-info-box {
  width: 55%;
  padding: 36px 40px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.card-info-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.room-name {
  font-size: 22px;
  font-weight: 800;
  color: #1a2b40;
  margin: 0;
  font-family: 'Georgia', serif;
}

.stock-indicator {
  background: rgba(39, 174, 96, 0.08);
  color: #27ae60;
  font-size: 11px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 4px;
  letter-spacing: 0.5px;
}

.stock-indicator.low-stock {
  background: rgba(231, 76, 60, 0.08);
  color: #e74c3c;
  animation: pulse-red-glow 2s infinite alternate;
}

@keyframes pulse-red-glow {
  0% { box-shadow: 0 0 0 0 rgba(231, 76, 60, 0.2); }
  100% { box-shadow: 0 0 0 6px rgba(231, 76, 60, 0); }
}

.room-intro {
  font-size: 13px;
  line-height: 1.6;
  color: #46566b;
  margin: 0 0 20px 0;
  height: 42px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.spec-tags {
  display: flex;
  gap: 16px;
  background: #fcfbf9;
  border-radius: 8px;
  padding: 10px 16px;
  margin-bottom: 20px;
  border: 1px solid rgba(22, 50, 79, 0.05);
}

.spec-tag-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.spec-label {
  font-size: 10px;
  color: #c3cddb;
  font-weight: 700;
  text-transform: uppercase;
}

.spec-val {
  font-size: 12px;
  color: #1a2b40;
  font-weight: 700;
}

.facility-badges {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.badge {
  font-size: 11px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 4px;
  border: 1px solid transparent;
}

.badge.active {
  background: rgba(22, 50, 79, 0.05);
  color: #16324f;
  border-color: rgba(22, 50, 79, 0.12);
}

.badge.inactive {
  background: #f7fafc;
  color: #c3cddb;
}

.go-detail-btn {
  background: #16324f !important;
  border-color: #16324f !important;
  color: #ffffff !important;
  font-weight: 700;
  border-radius: 8px;
  padding: 10px 24px;
  box-shadow: 0 4px 12px rgba(22, 50, 79, 0.15);
  align-self: flex-start;
}

.go-detail-btn:hover {
  background: #1a2b40 !important;
}

.btn-icon {
  margin-left: 6px;
}

@media (max-width: 992px) {
  .asymmetric-room-card,
  .asymmetric-room-card.row-reverse {
    flex-direction: column;
    height: auto;
  }

  .card-image-box,
  .card-info-box {
    width: 100%;
  }

  .card-image-box {
    height: 220px;
  }

  .card-info-box {
    padding: 24px;
  }

  .filter-panel {
    padding: 22px 20px 26px;
  }

  .filter-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .filter-row-label {
    width: auto;
    text-align: left;
  }
}
</style>
