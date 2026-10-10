<template>
  <div>
    <van-nav-bar title="价格看板" />

    <!-- 分类切换 -->
    <van-tabs v-model:active="activeName" @change="loadTrend">
      <van-tab v-for="c in allCategories" :key="c.id" :title="c.name" :name="c.id" />
    </van-tabs>

    <!-- 最新价 -->
    <div class="current" v-if="current">
      <span class="label">最新价</span>
      <span class="value">{{ current.price }}</span>
      <span class="unit">元/斤</span>
      <span class="date">{{ current.record_date }} · {{ current.region_name }}</span>
    </div>

    <!-- 趋势图 -->
    <div ref="chartEl" class="chart" />

    <!-- 同比环比 -->
    <van-cell-group inset style="margin-top: 12px">
      <van-cell title="环比（较上月）" :value="pctText(yoy?.mom_pct)" />
      <van-cell title="同比（较去年）" :value="pctText(yoy?.yoy_pct)" />
    </van-cell-group>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { getCategories } from '../api/auth'
import { getLatestPrices, getPriceTrend, getYoy } from '../api/price'

const activeName = ref(1)
const categories = ref([])
const latest = ref([])
const trend = ref([])
const yoy = ref(null)
const chartEl = ref(null)
let chart = null

const allCategories = computed(() => categories.value)
const current = computed(() =>
  latest.value.find((p) => p.category_id === activeName.value))

function pctText(v) {
  if (v === null || v === undefined) return '暂无'
  return `${v > 0 ? '涨' : v < 0 ? '跌' : '平'} ${Math.abs(v)}%`
}

async function loadTrend() {
  const cat = categories.value.find((c) => c.id === activeName.value)
  if (!cat) return
  const halfYearAgo = new Date(Date.now() - 180 * 86400000).toISOString().slice(0, 10)
  trend.value = await getPriceTrend({
    category_id: cat.id, region_id: 1, start_date: halfYearAgo,
  })
  yoy.value = await getYoy({ category_id: cat.id, region_id: 1 })
  renderChart(cat.name)
}

function renderChart(name) {
  if (!chartEl.value) return
  if (!chart) chart = echarts.init(chartEl.value)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 45, right: 15, top: 20, bottom: 30 },
    xAxis: { type: 'category', data: trend.value.map((p) => p.date) },
    yAxis: { type: 'value', scale: true, name: '元/斤' },
    series: [{ name, type: 'line', smooth: true, symbol: 'none',
               data: trend.value.map((p) => p.price),
               areaStyle: { opacity: 0.12 }, itemStyle: { color: '#1989fa' } }],
  }, true)
}

onMounted(async () => {
  categories.value = await getCategories()
  latest.value = await getLatestPrices({ region_id: 1 })
  if (categories.value.length) {
    activeName.value = categories.value[0].id
    await loadTrend()
  }
  window.addEventListener('resize', resize)
})

function resize() { chart && chart.resize() }
onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  chart && chart.dispose()
})
</script>

<style scoped>
.current { background: #fff; padding: 14px 16px; display: flex; align-items: baseline;
           gap: 6px; flex-wrap: wrap; }
.label { color: #646566; }
.value { font-size: 32px; font-weight: bold; color: #ee0a24; }
.unit { color: #969799; font-size: 13px; }
.date { color: #c8c9cc; font-size: 12px; margin-left: auto; }
.chart { height: 320px; background: #fff; margin-top: 2px; }
</style>
