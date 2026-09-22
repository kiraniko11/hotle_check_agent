<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowRight, Collection } from '@element-plus/icons-vue'

import { getUserFavorites, toggleFavorite } from '../api/rooms'

const router = useRouter()
const favorites = ref([])
const loading = ref(true)

// 加载收藏列表。
async function loadFavorites() {
  loading.value = true
  try {
    const response = await getUserFavorites()
    if (response.data && response.data.code === 200) {
      favorites.value = response.data.data
    }
  } finally {
    loading.value = false
  }
}

// 取消收藏并从列表移除。
async function handleRemoveFavorite(fav) {
  ElMessageBox.confirm(
    `确定取消收藏「${fav.room_type_detail.name}」吗？`,
    '取消收藏确认',
    { confirmButtonText: '确认取消', cancelButtonText: '再想想', type: 'warning' }
  ).then(async () => {
    const response = await toggleFavorite(fav.room_type)
    if (response.data && response.data.code === 200) {
      ElMessage.success('已取消收藏')
      favorites.value = favorites.value.filter(item => item.id !== fav.id)
    }
  }).catch(() => {})
}

onMounted(() => {
  loadFavorites()
})
</script>

<template>
  <main class="favorites-page">
    <div class="favorites-body">
      <header class="page-head">
        <span class="eyebrow">MY COLLECTION</span>
        <h1>我的收藏</h1>
        <p>收藏心仪房型，随时回到这里继续预订。</p>
      </header>

      <section v-loading="loading" class="favorites-grid">
        <el-empty
          v-if="!loading && favorites.length === 0"
          description="还没有收藏任何房型"
          class="empty-block"
        >
          <el-button class="browse-btn" @click="router.push('/rooms')">去逛逛客房</el-button>
        </el-empty>

        <article v-for="fav in favorites" :key="fav.id" class="favorite-card">
          <div class="favorite-cover" @click="router.push(`/rooms/${fav.room_type}`)">
            <img :src="fav.room_type_detail.cover_image" :alt="fav.room_type_detail.name" />
            <span class="cover-price">
              ¥{{ Math.round(fav.room_type_detail.price) }} <em>/ 晚</em>
            </span>
          </div>

          <div class="favorite-info">
            <div class="info-head">
              <h3>{{ fav.room_type_detail.name }}</h3>
              <span class="collect-date">收藏于 {{ String(fav.created_at).substring(0, 10) }}</span>
            </div>

            <p class="info-desc">{{ fav.room_type_detail.description }}</p>

            <div class="spec-row">
              <span>{{ fav.room_type_detail.area }} ㎡</span>
              <span class="dot">·</span>
              <span>{{ fav.room_type_detail.bed_type }}</span>
              <span class="dot">·</span>
              <span>可住 {{ fav.room_type_detail.capacity }} 人</span>
            </div>

            <div class="stock-row">
              <el-icon class="stock-icon"><Collection /></el-icon>
              剩余 {{ fav.room_type_detail.remaining_stock }} 间可预订
            </div>

            <div class="favorite-actions">
              <button class="book-btn" type="button" @click="router.push(`/rooms/${fav.room_type}`)">
                立即预订
                <el-icon><ArrowRight /></el-icon>
              </button>
              <button class="remove-btn" type="button" @click="handleRemoveFavorite(fav)">
                取消收藏
              </button>
            </div>
          </div>
        </article>
      </section>
    </div>
  </main>
</template>

<style scoped>
.favorites-page {
  min-height: 100vh;
  background-color: #f4f7fb;
  padding-bottom: 80px;
}

.favorites-body {
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
  margin: 10px 0;
  font-family: 'Georgia', serif;
}

.page-head p {
  font-size: 14px;
  color: #8494ab;
  margin: 0;
}

.favorites-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(440px, 1fr));
  gap: 26px;
  min-height: 200px;
}

.empty-block {
  grid-column: 1 / -1;
}

.browse-btn {
  background: #16324f !important;
  border-color: #16324f !important;
  color: #ffffff !important;
  font-weight: 700;
}

.favorite-card {
  background: #ffffff;
  border: 1px solid rgba(22, 50, 79, 0.08);
  border-radius: 16px;
  overflow: hidden;
  display: flex;
  box-shadow: 0 8px 26px rgba(22, 50, 79, 0.03);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.favorite-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 16px 36px rgba(79, 142, 247, 0.16);
}

.favorite-cover {
  position: relative;
  width: 42%;
  cursor: pointer;
  overflow: hidden;
}

.favorite-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.6s ease;
  display: block;
}

.favorite-card:hover .favorite-cover img {
  transform: scale(1.05);
}

.cover-price {
  position: absolute;
  left: 14px;
  bottom: 14px;
  background: rgba(22, 50, 79, 0.88);
  color: #ffffff;
  font-size: 16px;
  font-weight: 800;
  padding: 6px 12px;
  border-radius: 20px;
  font-family: 'Georgia', serif;
}

.cover-price em {
  font-size: 10px;
  font-style: normal;
  opacity: 0.75;
  font-weight: 500;
}

.favorite-info {
  flex: 1;
  padding: 22px 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-head {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.info-head h3 {
  font-size: 19px;
  font-weight: 800;
  color: #1a2b40;
  margin: 0;
  font-family: 'Georgia', serif;
}

.collect-date {
  font-size: 11px;
  color: #c3cddb;
  font-weight: 600;
}

.info-desc {
  font-size: 13px;
  line-height: 1.6;
  color: #46566b;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.spec-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  font-size: 12px;
  color: #8494ab;
  align-items: center;
}

.spec-row .dot {
  color: #4f8ef7;
}

.stock-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 700;
  color: #27ae60;
}

.stock-icon {
  font-size: 14px;
}

.favorite-actions {
  display: flex;
  gap: 10px;
  margin-top: auto;
}

.book-btn,
.remove-btn {
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

.book-btn {
  flex: 1;
  background: #16324f;
  border: 1px solid #16324f;
  color: #ffffff;
}

.book-btn:hover {
  background: #1a2b40;
}

.remove-btn {
  background: transparent;
  border: 1px solid rgba(22, 50, 79, 0.18);
  color: #6b7f99;
  padding: 0 18px;
}

.remove-btn:hover {
  border-color: #e74c3c;
  color: #e74c3c;
}

@media (max-width: 992px) {
  .favorites-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .favorite-card {
    flex-direction: column;
  }

  .favorite-cover {
    width: 100%;
    height: 200px;
  }
}
</style>
