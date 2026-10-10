<template>
  <div>
    <!-- 指标卡：四类牛羊价格最新值 -->
    <el-row :gutter="16">
      <el-col :span="6" v-for="item in latestLivestock" :key="item.category_id">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-name">{{ item.category_name }}（{{ item.region_name }}）</div>
          <div class="stat-value">{{ item.price }} <small>元/斤</small></div>
          <div class="stat-date">
            {{ item.record_date }}
            <span :title="item.source_detail || item.source" class="src-tag"
                  :class="'src-' + (item.source || 'manual')">{{ srcLabel(item.source) }}</span>
          </div>
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

    <div class="src-tip">当前显示定西周报数据</div>
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

// 数据来源标签：gov=政府绿 derived=反推灰 index=指数蓝 manual=示例黄
function srcLabel(s) {
  return { gov: '政府', derived: '反推', index: '指数', manual: '示例' }[s] || s
}

const trendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  xAxis: { type: 'category', data: trend.value.map((p) => p.date) },
  yAxis: { type: 'value', name: '元/斤', scale: true },
  series: [{ name: '活牛', type: 'line', data: trend.value.map((p) => p.price),
             smooth: true, areaStyle: { opacity: 0.15 } }],
  grid: { left: 50, right: 20, top: 30, bottom: 30 },
}))

onMounted(async () => {
  // 最新价（牲畜 + 饲料）与活牛趋势；默认定西（当前唯一有真实周报数据的地区）
  const REGION = 12
  try {
    const data = await getLatestPrices({ region_id: REGION })
    latestLivestock.value = data.filter((d) => d.type === 'livestock')
  } catch (e) { /* 数据库未初始化时空列表 */ }
  try {
    const res = await getLatestFeed({ region_id: REGION })
    latestFeed.value = res.items
  } catch (e) { /* 同上 */ }
  try {
    const oneYearAgo = new Date(Date.now() - 365 * 86400000).toISOString().slice(0, 10)
    const res = await getPriceTrend({ category_id: 1, region_id: REGION, start_date: oneYearAgo })
    trend.value = res.points
  } catch (e) { /* 同上 */ }
})
</script>

<style scoped>
.stat-card { text-align: center; }
.stat-name { color: #909399; font-size: 14px; }
.stat-value { font-size: 30px; font-weight: bold; color: #409eff; margin: 8px 0; }
.stat-value small { font-size: 13px; color: #909399; font-weight: normal; }
.stat-date { color: #c0c4cc; font-size: 12px; }
.src-tag { margin-left: 4px; padding: 0 4px; border-radius: 3px; font-size: 10px; color: #fff; }
.src-gov { background: #67c23a; }
.src-derived { background: #909399; }
.src-index { background: #409eff; }
.src-manual { background: #e6a23c; }
.src-tip { text-align: center; color: #c0c4cc; font-size: 12px; margin-top: 16px; }
</style>
