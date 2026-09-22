<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchRoomTypes } from '../api/rooms'

const router = useRouter()
const roomTypes = ref([])
const loading = ref(true)

// 获取后端房型数据。
async function loadCarouselData() {
  try {
    const response = await fetchRoomTypes()
    if (response.data && response.data.code === 200) {
      roomTypes.value = response.data.data
    }
  } catch (err) {
    console.error('加载轮播图房型数据失败', err)
  } finally {
    loading.value = false
  }
}

// 路由跳转。
function goDetail(id) {
  router.push(`/rooms/${id}`)
}

onMounted(() => {
  loadCarouselData()
})
</script>

<template>
  <div v-loading="loading" class="rooms-carousel-wrapper">
    <el-carousel
      v-if="roomTypes.length > 0"
      height="450px"
      arrow="always"
      indicator-position="outside"
    >
      <el-carousel-item v-for="item in roomTypes" :key="item.id">
        <div class="carousel-slide-content">
          <!-- 左侧燕麦色文字详情区 -->
          <div class="slide-text-info">
            <span class="slide-tag">本月推荐</span>
            <h2 class="slide-title">{{ item.name }}</h2>
            <p class="slide-desc">{{ item.description }}</p>

            <div class="slide-spec-row">
              <span class="spec-label">面积: {{ item.area }}㎡</span>
              <span class="spec-divider">/</span>
              <span class="spec-label">床型: {{ item.bed_type }}</span>
              <span class="spec-divider">/</span>
              <span class="spec-label">容量: {{ item.capacity }}位宾客</span>
            </div>

            <div class="slide-price-box">
              <span class="price-symbol">¥</span>
              <span class="price-val">{{ Math.round(item.price) }}</span>
              <span class="price-unit">/ 每晚起</span>
            </div>

            <div class="slide-actions">
              <el-button type="primary" class="slide-cta-btn" @click="goDetail(item.id)">
                查看空间详情与房号
              </el-button>
            </div>
          </div>

          <!-- 右侧高清展示图 -->
          <div class="slide-image-box">
            <img :src="item.cover_image" :alt="item.name" />
          </div>
        </div>
      </el-carousel-item>
    </el-carousel>
  </div>
</template>

<style scoped>
.rooms-carousel-wrapper {
  background: #ffffff;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 10px 35px rgba(22, 50, 79, 0.05);
  margin-bottom: 30px;
  border: 1px solid rgba(22, 50, 79, 0.08);
}

.carousel-slide-content {
  display: flex;
  height: 100%;
  width: 100%;
}

.slide-text-info {
  flex: 0.9;
  padding: 48px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  background-color: #eaf1fa;
}

.slide-tag {
  font-size: 11px;
  font-weight: 700;
  color: #16324f;
  letter-spacing: 2px;
  margin-bottom: 14px;
}

.slide-title {
  font-size: 28px;
  font-weight: 800;
  color: #1a2b40;
  margin: 0 0 16px 0;
  font-family: 'Georgia', serif;
}

.slide-desc {
  font-size: 14px;
  line-height: 1.7;
  color: #46566b;
  margin: 0 0 24px 0;
  height: 72px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.slide-spec-row {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: #8494ab;
  margin-bottom: 24px;
}

.spec-divider {
  opacity: 0.5;
}

.slide-price-box {
  display: flex;
  align-items: baseline;
  gap: 4px;
  color: #2f6fd8;
  margin-bottom: 30px;
}

.price-symbol {
  font-size: 14px;
  font-weight: 700;
}

.price-val {
  font-size: 30px;
  font-weight: 800;
  font-family: 'Georgia', serif;
}

.price-unit {
  font-size: 12px;
  color: #8494ab;
  font-weight: 500;
}

.slide-cta-btn {
  background: transparent !important;
  border: 1px solid #16324f !important;
  color: #16324f !important;
  font-weight: 700;
  padding: 12px 28px;
  height: auto;
  border-radius: 8px;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.slide-cta-btn:hover {
  background: #16324f !important;
  color: #ffffff !important;
  box-shadow: 0 4px 12px rgba(22, 50, 79, 0.2);
}

.slide-image-box {
  flex: 1.1;
  overflow: hidden;
  position: relative;
}

.slide-image-box img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.8s ease;
}

.carousel-slide-content:hover .slide-image-box img {
  transform: scale(1.04);
}

.slide-image-box::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, #eaf1fa 0%, rgba(234, 241, 250, 0) 15%);
  pointer-events: none;
}
</style>
