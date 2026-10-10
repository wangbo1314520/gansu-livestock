<template>
  <el-card shadow="never">
    <el-form inline>
      <el-form-item label="分类">
        <el-select v-model="categoryId" style="width: 120px" @change="load">
          <el-option v-for="c in livestockCategories" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="地区">
        <el-select v-model="regionId" style="width: 140px" @change="load">
          <el-option v-for="r in regions" :key="r.id" :label="r.name" :value="r.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="范围">
        <el-radio-group v-model="range" @change="load">
          <el-radio-button value="90">近3月</el-radio-button>
          <el-radio-button value="180">近半年</el-radio-button>
          <el-radio-button value="365">近一年</el-radio-button>
        </el-radio-group>
      </el-form-item>
      <el-form-item label="包含示例数据">
        <el-switch v-model="includeSample" @change="load" />
      </el-form-item>
      <el-form-item label="数据源">
        <el-select v-model="sources" multiple collapse-tags style="width: 200px">
          <el-option label="政府监测" value="gov" />
          <el-option label="反推补全" value="derived" />
          <el-option label="红牛指数" value="index" />
          <el-option label="示例数据" value="manual" />
        </el-select>
      </el-form-item>
    </el-form>

    <ChartCard title="价格趋势" :option="option" :height="420" />

    <!-- 同比环比卡片 -->
    <el-descriptions v-if="yoy" title="同比环比" :column="4" border style="margin-top: 16px">
      <el-descriptions-item label="近7天均价">{{ yoy.current }} 元/斤</el-descriptions-item>
      <el-descriptions-item label="环比（上月）">
        <span :class="pctClass(yoy.mom_pct)">{{ pctText(yoy.mom_pct) }}</span>
      </el-descriptions-item>
      <el-descriptions-item label="同比（去年）">
        <span :class="pctClass(yoy.yoy_pct)">{{ pctText(yoy.yoy_pct) }}</span>
      </el-descriptions-item>
      <el-descriptions-item label="基准日期">{{ yoy.ref_date }}</el-descriptions-item>
    </el-descriptions>
  </el-card>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import ChartCard from '../components/ChartCard.vue'
import { getPriceTrend, getYoy } from '../api/price'
import { getRegions, getCategories } from '../api/auth'

const categoryId = ref(1)
const regionId = ref(1)
const range = ref('365')
const includeSample = ref(false)
const trend = ref([])
const yoy = ref(null)
const regions = ref([])
const categories = ref([])

const livestockCategories = computed(() => categories.value.filter((c) => c.type === 'livestock'))

// 数据源多选筛选（默认全选；图表按筛选结果绘制）
const sources = ref(['gov', 'derived', 'index', 'manual'])
const SRC_META = {
  gov: { label: '政府监测', color: '#409eff', detail: '政府价格监测周报（真实观测）' },
  derived: { label: '反推补全', color: '#909399', detail: '由肉价反推的衍生数据（预测补全用）' },
  index: { label: '红牛指数', color: '#67c23a', detail: '新华·平凉红牛价格指数（月度）' },
  manual: { label: '示例数据', color: '#e6a23c', detail: '开发用示例数据（非真实）' },
}
const ptSrc = (p) => {
  // 点 source 可能是多来源逗号串，取第一个非空值归一到四类
  const s = (p.source || 'manual').split(',')[0].trim()
  return SRC_META[s] ? s : 'manual'
}
const filtered = computed(() =>
  trend.value.filter((p) => sources.value.includes(ptSrc(p))))

// 各来源一条 series（与共享 x 轴全长度对齐，非本系列的点置 null）
const seriesOf = (key) => filtered.value.map((p) => (ptSrc(p) === key ? p.price : null))

const option = computed(() => ({
  tooltip: {
    trigger: 'axis',
    formatter: (params) => {
      const date = params[0]?.axisValueLabel || ''
      const lines = params.filter((v) => v.value != null).map((v) => {
        const meta = Object.values(SRC_META).find((m) => m.label === v.seriesName)
        return `${v.marker} ${v.seriesName}：<b>${v.value}</b> 元/斤<br/>
<span style="color:#909399;font-size:11px">${meta ? meta.detail : ''}</span>`
      })
      return lines.length ? `${date}<br/>${lines.join('<br/>')}` : date
    },
  },
  legend: { data: Object.values(SRC_META).map((m) => m.label) },   // 可点击切换数据源
  xAxis: {
    type: 'category',
    data: filtered.value.map((p) => p.date),
    axisLabel: {
      formatter: (d) => d.slice(0, 7),     // YYYY-MM
      rotate: 30,
    },
  },
  yAxis: { type: 'value', name: '元/斤', scale: true },
  dataZoom: [{ type: 'inside' }, { type: 'slider' }],
  series: [
    { name: SRC_META.gov.label, type: 'line', smooth: true, symbol: 'circle',
      connectNulls: false, itemStyle: { color: SRC_META.gov.color },
      lineStyle: { color: SRC_META.gov.color },
      data: seriesOf('gov') },
    { name: SRC_META.derived.label, type: 'line', smooth: true, symbol: 'diamond', symbolSize: 7,
      connectNulls: true,
      lineStyle: { type: 'dashed', color: SRC_META.derived.color },
      itemStyle: { color: SRC_META.derived.color },
      data: seriesOf('derived') },
    { name: SRC_META.index.label, type: 'line', symbol: 'triangle', symbolSize: 8,
      connectNulls: true,
      lineStyle: { type: 'dotted', width: 2, color: SRC_META.index.color },
      itemStyle: { color: SRC_META.index.color },
      data: seriesOf('index') },
    { name: SRC_META.manual.label, type: 'line', smooth: true, symbol: 'none',
      lineStyle: { width: 1, color: SRC_META.manual.color },
      itemStyle: { color: SRC_META.manual.color },
      data: seriesOf('manual') },
  ],
  grid: { left: 50, right: 20, top: 40, bottom: 50 },
}))

async function load() {
  const startDate = new Date(Date.now() - Number(range.value) * 86400000).toISOString().slice(0, 10)
  const res = await getPriceTrend({
    category_id: categoryId.value, region_id: regionId.value, start_date: startDate,
    include_sample: includeSample.value,
  })
  trend.value = res.points
  yoy.value = await getYoy({
    category_id: categoryId.value, region_id: regionId.value,
    include_sample: includeSample.value,
  })
}

function pctText(v) {
  return v === null || v === undefined ? '暂无' : `${v > 0 ? '+' : ''}${v}%`
}
function pctClass(v) {
  if (v === null || v === undefined) return ''
  return v > 0 ? 'up' : 'down'
}

onMounted(async () => {
  regions.value = await getRegions()
  categories.value = await getCategories()
  load()
})
</script>

<style scoped>
.up { color: #f56c6c; }
.down { color: #67c23a; }
</style>
