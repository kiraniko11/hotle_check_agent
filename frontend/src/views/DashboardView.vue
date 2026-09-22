<script setup>
import { onBeforeUnmount, onMounted, ref, shallowRef } from 'vue'
import { useRouter } from 'vue-router'
import { InfoFilled, Opportunity, House, TrendCharts } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

import RoomsCarousel from '../components/RoomsCarousel.vue'
import { fetchRoomStats } from '../api/rooms'

const router = useRouter()

const stats = ref(null)
const statsLoading = ref(true)
// 使用 shallowRef 保存 ECharts 实例，避免被深度代理影响渲染性能。
const stockChartRef = ref(null)
const statusChartRef = ref(null)
const stockChart = shallowRef(null)
const statusChart = shallowRef(null)

function goToRooms() {
  router.push('/rooms')
}

// 渲染各房型库存对比柱状图。
function renderStockChart(distribution) {
  if (!stockChartRef.value) return
  stockChart.value = echarts.init(stockChartRef.value)
  stockChart.value.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: ['总库存', '可预订'], top: 0, textStyle: { color: '#46566b' } },
    grid: { left: 40, right: 20, top: 46, bottom: 60 },
    xAxis: {
      type: 'category',
      data: distribution.map((item) => item.name),
      axisLabel: { color: '#8494ab', fontSize: 11, interval: 0, rotate: 22 },
      axisLine: { lineStyle: { color: 'rgba(22,50,79,0.15)' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#8494ab', fontSize: 11 },
      splitLine: { lineStyle: { color: 'rgba(22,50,79,0.06)' } },
    },
    series: [
      {
        name: '总库存',
        type: 'bar',
        barWidth: 16,
        itemStyle: { color: '#4f8ef7', borderRadius: [4, 4, 0, 0] },
        data: distribution.map((item) => item.total_stock),
      },
      {
        name: '可预订',
        type: 'bar',
        barWidth: 16,
        itemStyle: { color: '#16324f', borderRadius: [4, 4, 0, 0] },
        data: distribution.map((item) => item.remaining_stock),
      },
    ],
  })
}

// 渲染订单状态分布饼图。
function renderStatusChart(distribution) {
  if (!statusChartRef.value) return
  statusChart.value = echarts.init(statusChartRef.value)
  statusChart.value.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} 单 ({d}%)' },
    legend: { bottom: 0, textStyle: { color: '#46566b' } },
    color: ['#16324f', '#27ae60', '#4f8ef7', '#c3cddb'],
    series: [
      {
        name: '订单状态',
        type: 'pie',
        radius: ['42%', '66%'],
        center: ['50%', '44%'],
        avoidLabelOverlap: true,
        itemStyle: { borderColor: '#ffffff', borderWidth: 2 },
        label: { color: '#46566b', fontSize: 11 },
        data: distribution.map((item) => ({
          name: item.status_display,
          value: item.count,
        })),
      },
    ],
  })
}

function handleResize() {
  stockChart.value?.resize()
  statusChart.value?.resize()
}

// 拉取统计数据并初始化图表。
async function loadStats() {
  try {
    const response = await fetchRoomStats()
    if (response.data?.code === 200) {
      stats.value = response.data.data
      renderStockChart(stats.value.type_distribution || [])
      renderStatusChart(stats.value.status_distribution || [])
    }
  } finally {
    statsLoading.value = false
  }
}

onMounted(() => {
  loadStats()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  stockChart.value?.dispose()
  statusChart.value?.dispose()
})
</script>

<template>
  <main class="dashboard-container">
    <!-- 巨幕区 (Hero Banner) -->
    <section class="hotel-hero-section">
      <div class="hero-overlay"></div>
      <div class="hero-content">
        <span class="hero-eyebrow">欢迎光临</span>
        <h1 class="hero-title">住得干净舒心 &bull; 价格简单实在</h1>
        <p class="hero-desc">房间每天打扫，热水 24 小时有，无线网全楼覆盖，前台随时有人。需要订房可以自己选，也可以让 AI 助手帮您订。</p>
        <el-button type="primary" size="large" class="hero-cta-btn" @click="goToRooms">
          去看看空房
        </el-button>
      </div>
    </section>

    <div class="dashboard-body">
      <!-- 动态数据房型轮播图组件 -->
      <section class="carousel-section" aria-label="推荐展示">
        <div class="section-header">
          <span class="sub-title">房型展示</span>
          <h2 class="title">房型一览</h2>
          <p class="desc">房型图片和价格都是数据库实时数据，左右滑动查看参数，看中了直接下单。</p>
        </div>
        <RoomsCarousel />
      </section>

      <!-- 实时数据看板：ECharts 图表 -->
      <section v-loading="statsLoading" class="analytics-section">
        <div class="section-header">
          <span class="sub-title">运营数据</span>
          <h2 class="title">实时房态与订单看板</h2>
          <p class="desc">数据由后端聚合查询实时返回，帮助宾客与运营人员共同掌握库存与订单状态。</p>
        </div>

        <div class="metric-strip">
          <div class="metric-pill">
            <span>在售房型</span>
            <strong>{{ stats?.room_type_count ?? 0 }}</strong>
          </div>
          <div class="metric-pill">
            <span>物理客房</span>
            <strong>{{ stats?.room_count ?? 0 }}</strong>
          </div>
          <div class="metric-pill">
            <span>可预订库存</span>
            <strong>{{ stats?.remaining_stock ?? 0 }}</strong>
          </div>
          <div class="metric-pill">
            <span>累计订单</span>
            <strong>{{ stats?.booking_count ?? 0 }}</strong>
          </div>
          <div class="metric-pill">
            <span>平均房价</span>
            <strong>¥{{ Math.round(stats?.average_price ?? 0) }}</strong>
          </div>
        </div>

        <div class="charts-grid">
          <div class="chart-card">
            <div class="chart-head">
              <el-icon><TrendCharts /></el-icon>
              <h3>各房型库存对比</h3>
            </div>
            <div ref="stockChartRef" class="chart-canvas"></div>
          </div>
          <div class="chart-card">
            <div class="chart-head">
              <el-icon><TrendCharts /></el-icon>
              <h3>订单状态分布</h3>
            </div>
            <div ref="statusChartRef" class="chart-canvas"></div>
          </div>
        </div>
      </section>

      <!-- 酒店服务模块 -->
      <section id="features-section" class="hotel-features-section">
        <div class="section-header">
          <span class="sub-title">酒店服务</span>
          <h2 class="title">友家快捷酒店的服务</h2>
          <p class="desc">不搞虚的，该有的都有，也不多收一分冤枉钱。</p>
        </div>

        <div class="features-grid">
          <div class="feature-item-card">
            <div class="feature-icon-box">
              <el-icon><Opportunity /></el-icon>
            </div>
            <h3>免费无线网络</h3>
            <p>全楼覆盖无线网，房间和大厅信号都很好，刷视频、开视频会议都不卡。</p>
          </div>

          <div class="feature-item-card">
            <div class="feature-icon-box">
              <el-icon><InfoFilled /></el-icon>
            </div>
            <h3>干净床品</h3>
            <p>床单被罩一客一换，热水 24 小时供应，空调随开随用，晚上睡觉踏实。</p>
          </div>

          <div class="feature-item-card">
            <div class="feature-icon-box">
              <el-icon><House /></el-icon>
            </div>
            <h3>退房不排队</h3>
            <p>退房时报一下房号，查完房间就能走，押金原路退回，不用在大堂干等。</p>
          </div>
        </div>
      </section>
    </div>
  </main>
</template>

<style scoped>
.dashboard-container {
  min-height: 100vh;
  background-color: #f4f7fb;
  padding-bottom: 80px;
}

/* 巨幕 Hero 视觉区 */
.hotel-hero-section {
  height: 540px;
  position: relative;
  background-image: url('../assets/photo-1542314831-068cd1dbfeeb.avif');
  background-size: cover;
  background-position: center;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: #ffffff;
}

.hero-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(22, 50, 79, 0.45) 0%, rgba(244, 247, 251, 0.9) 75%, #f4f7fb 100%);
  z-index: 1;
}

.hero-content {
  position: relative;
  z-index: 2;
  max-width: 850px;
  padding: 0 20px;
  margin-top: -30px;
}

.hero-eyebrow {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 4px;
  color: #16324f;
  text-transform: uppercase;
  display: block;
  margin-bottom: 16px;
}

.hero-title {
  font-size: 40px;
  font-weight: 800;
  margin: 0 0 20px 0;
  letter-spacing: 1px;
  color: #16324f;
}

.hero-desc {
  font-size: 15px;
  line-height: 1.8;
  color: #46566b;
  margin: 0 0 32px 0;
  max-width: 90%;
  margin-inline: auto;
}

.hero-cta-btn {
  background: #16324f !important;
  border-color: #16324f !important;
  font-weight: 700;
  padding: 15px 36px;
  height: auto;
  border-radius: 30px;
  color: #ffffff !important;
  box-shadow: 0 6px 20px rgba(22, 50, 79, 0.2);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.hero-cta-btn:hover {
  transform: translateY(-2px);
  background: #1a2b40 !important;
  box-shadow: 0 10px 25px rgba(22, 50, 79, 0.3);
}

/* 主体容器 */
.dashboard-body {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 24px 40px 24px;
}

/* 模块通用标题 */
.section-header {
  text-align: center;
  max-width: 650px;
  margin: 0 auto 36px auto;
}

.section-header .sub-title {
  font-size: 11px;
  font-weight: 700;
  color: #16324f;
  letter-spacing: 2px;
  text-transform: uppercase;
  display: block;
  margin-bottom: 8px;
}

.section-header .title {
  font-size: 26px;
  font-weight: 800;
  color: #1a2b40;
  margin: 0 0 12px 0;
  font-family: 'Georgia', serif;
}

.section-header .desc {
  font-size: 14px;
  line-height: 1.6;
  color: #8494ab;
  margin: 0;
}

/* 轮播展示 */
.carousel-section {
  margin-bottom: 64px;
}

/* 数据看板 */
.analytics-section {
  margin-bottom: 64px;
}

.metric-strip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 14px;
  margin-bottom: 22px;
}

.metric-pill {
  background: #ffffff;
  border: 1px solid rgba(22, 50, 79, 0.08);
  border-radius: 14px;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  box-shadow: 0 6px 20px rgba(22, 50, 79, 0.02);
}

.metric-pill span {
  font-size: 12px;
  color: #8494ab;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.metric-pill strong {
  font-size: 24px;
  font-weight: 800;
  color: #16324f;
  font-family: 'Georgia', serif;
}

.charts-grid {
  display: grid;
  grid-template-columns: 1.35fr 1fr;
  gap: 20px;
}

.chart-card {
  background: #ffffff;
  border: 1px solid rgba(22, 50, 79, 0.08);
  border-radius: 16px;
  padding: 20px 22px;
  box-shadow: 0 10px 30px rgba(22, 50, 79, 0.03);
}

.chart-head {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #4f8ef7;
  margin-bottom: 6px;
}

.chart-head h3 {
  font-size: 14px;
  font-weight: 800;
  color: #1a2b40;
  margin: 0;
}

.chart-canvas {
  width: 100%;
  height: 300px;
}

/* 品牌专属服务模块：蓝色微光特效 */
.hotel-features-section {
  border-top: 1px solid rgba(22, 50, 79, 0.12);
  padding-top: 56px;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 30px;
}

.feature-item-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 30px;
  text-align: center;
  border: 1px solid rgba(22, 50, 79, 0.08);
  box-shadow: 0 6px 20px rgba(22, 50, 79, 0.02);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.feature-item-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 25px rgba(79, 142, 247, 0.15);
}

.feature-icon-box {
  width: 60px;
  height: 60px;
  background: rgba(22, 50, 79, 0.06);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px auto;
  color: #16324f;
  font-size: 24px;
}

.feature-item-card h3 {
  font-size: 18px;
  font-weight: 800;
  color: #1a2b40;
  margin: 0 0 12px 0;
}

.feature-item-card p {
  font-size: 13px;
  line-height: 1.6;
  color: #46566b;
  margin: 0;
}

@media (max-width: 992px) {
  .features-grid,
  .charts-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 600px) {
  .hero-title {
    font-size: 26px;
  }
}
</style>
