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
const trend = ref([])
const yoy = ref(null)
const regions = ref([])
const categories = ref([])

const livestockCategories = computed(() => categories.value.filter((c) => c.type === 'livestock'))

const option = computed(() => ({
  tooltip: { trigger: 'axis' },
  xAxis: { type: 'category', data: trend.value.map((p) => p.date) },
  yAxis: { type: 'value', name: '元/斤', scale: true },
  dataZoom: [{ type: 'inside' }, { type: 'slider' }],
  series: [{ type: 'line', smooth: true, symbol: 'none',
             data: trend.value.map((p) => p.price),
             markPoint: {
               data: [
                 { type: 'max', name: '最高' },
                 { type: 'min', name: '最低' },
               ],
             } }],
  grid: { left: 50, right: 20, top: 30, bottom: 50 },
}))

async function load() {
  const startDate = new Date(Date.now() - Number(range.value) * 86400000).toISOString().slice(0, 10)
  trend.value = await getPriceTrend({
    category_id: categoryId.value, region_id: regionId.value, start_date: startDate,
  })
  yoy.value = await getYoy({
    category_id: categoryId.value, region_id: regionId.value,
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
