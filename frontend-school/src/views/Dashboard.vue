<template>
  <div>
    <!-- 指标卡：活牛 / 活羊 / 玉米 / 豆粕（核心关注四项） -->
    <el-row :gutter="16">
      <el-col :span="6" v-for="item in coreCards" :key="item.category_id">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-name">{{ item.category_name }}（{{ item.region_name }}）</div>
          <div class="stat-value">{{ item.price }} <small>元/斤</small></div>
          <div class="stat-mom" :class="(item.momPct || 0) >= 0 ? 'up' : 'down'">
            环比 {{ item.momPct == null ? "—" : (item.momPct > 0 ? "+" : "") + item.momPct + "%" }}
          </div>
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

    <div class="src-tip">数据源：定西周报（更新至 {{ latestDate || "—" }}）</div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import ChartCard from '../components/ChartCard.vue'
import { getLatestPrices, getPriceTrend, getYoy } from '../api/price'
import { getLatestFeed } from '../api/feed'

const latestAll = ref([])      // price/latest 全分类（取核心四类）
const latestFeed = ref([])
const trend = ref([])
const yoyMap = ref({})        // {category_id: mom_pct}

// 核心关注四项：活牛、活羊、玉米、豆粕
const CARDS = [1, 3, 5, 6]
const coreCards = computed(() =>
  latestAll.value.filter((p) => CARDS.includes(p.category_id))
    .map((p) => ({ ...p, momPct: yoyMap.value[p.category_id] })))
const latestDate = computed(() =>
  coreCards.value.length ? coreCards.value[0].record_date : '')

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
    latestAll.value = await getLatestPrices({ region_id: REGION })
    // 环比（上月）：逐核心分类取 mom_pct，单项失败不影响展示
    for (const cid of CARDS) {
      try {
        const y = await getYoy({ category_id: cid, region_id: REGION })
        yoyMap.value[cid] = y ? y.mom_pct : null
      } catch (e) { yoyMap.value[cid] = null }
    }
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
.stat-mom { font-size: 12px; margin: 2px 0; }
.up { color: #f56c6c; }
.down { color: #67c23a; }
.src-tip { text-align: center; color: #c0c4cc; font-size: 12px; margin-top: 16px; }
</style>
