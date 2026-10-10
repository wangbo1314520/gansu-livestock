<template>
  <div>
    <!-- 指标卡：四类牛羊价格最新值 -->
    <el-row :gutter="16">
      <el-col :span="6" v-for="item in latestLivestock" :key="item.category_id">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-name">{{ item.category_name }}（{{ item.region_name }}）</div>
          <div class="stat-value">{{ item.price }} <small>元/斤</small></div>
          <div class="stat-date">{{ item.record_date }} · {{ item.source }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 活牛全省趋势 -->
    <ChartCard title="活牛价格趋势（甘肃省，近一年）" :option="trendOption" :height="380"
               style="margin-top: 16px" />

    <!-- 饲料价格一览 -->
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="12" v-for="f in latestFeed" :key="f.category_id">
        <el-card shadow="hover">
          <div class="stat-name">{{ f.feed_name }}（{{ f.region_name }}）</div>
          <div class="stat-value">{{ f.price }} <small>元/斤</small></div>
          <div class="stat-date">约 {{ f.price_per_kg }} 元/kg · {{ f.record_date }}</div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import ChartCard from '../components/ChartCard.vue'
import { getLatestPrices, getPriceTrend } from '../api/price'
import { getLatestFeed } from '../api/feed'

const latestLivestock = ref([])
const latestFeed = ref([])
const trend = ref([])

const trendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  xAxis: { type: 'category', data: trend.value.map((p) => p.date) },
  yAxis: { type: 'value', name: '元/斤', scale: true },
  series: [{ name: '活牛', type: 'line', data: trend.value.map((p) => p.price),
             smooth: true, areaStyle: { opacity: 0.15 } }],
  grid: { left: 50, right: 20, top: 30, bottom: 30 },
}))

onMounted(async () => {
  // 最新价（牲畜 + 饲料）与活牛趋势；空数据时页面显示空卡片属正常
  try {
    const data = await getLatestPrices({ region_id: 1 })
    latestLivestock.value = data.filter((d) => d.type === 'livestock')
  } catch (e) { /* 数据库未初始化时空列表 */ }
  try {
    latestFeed.value = await getLatestFeed({ region_id: 1 })
  } catch (e) { /* 同上 */ }
  try {
    const oneYearAgo = new Date(Date.now() - 365 * 86400000).toISOString().slice(0, 10)
    trend.value = await getPriceTrend({ category_id: 1, region_id: 1, start_date: oneYearAgo })
  } catch (e) { /* 同上 */ }
})
</script>

<style scoped>
.stat-card { text-align: center; }
.stat-name { color: #909399; font-size: 14px; }
.stat-value { font-size: 30px; font-weight: bold; color: #409eff; margin: 8px 0; }
.stat-value small { font-size: 13px; color: #909399; font-weight: normal; }
.stat-date { color: #c0c4cc; font-size: 12px; }
</style>
