<template>
  <el-card shadow="never">
    <el-form inline>
      <el-form-item label="分类">
        <el-select v-model="categoryId" style="width: 120px">
          <el-option v-for="c in livestockCategories" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="地区">
        <el-select v-model="regionId" style="width: 140px">
          <el-option v-for="r in regions" :key="r.id" :label="r.name" :value="r.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="模型">
        <el-radio-group v-model="model">
          <el-radio-button value="arima">ARIMA</el-radio-button>
          <el-radio-button value="arimax">ARIMAX（含饲料变量）</el-radio-button>
        </el-radio-group>
      </el-form-item>
      <el-form-item label="预测天数">
        <el-input-number v-model="days" :min="7" :max="90" :step="7" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="loading" @click="runPredict">开始预测</el-button>
      </el-form-item>
    </el-form>

    <!-- 顶部精度摘要 -->
    <div v-if="metrics" class="metric-bar">
      <span>MAPE <b>{{ metrics.mape }}%</b></span>
      <el-tag size="small"
              :type="metrics.grade === '优秀' ? 'success' : metrics.grade === '良好' ? 'warning' : 'info'">
        {{ metrics.grade }}
      </el-tag>
      <span style="color:#909399">模型：{{ model === 'arimax' ? 'ARIMAX（含饲料变量）' : 'ARIMA' }}</span>
    </div>

    <ChartCard title="历史价格与预测（阴影为95%置信区间，预测段为虚线）"
               :option="option" :height="440" />

    <!-- 精度指标 -->
    <el-descriptions v-if="metrics" title="回测精度（最近30天留出法）" :column="4" border
                     style="margin-top: 16px">
      <el-descriptions-item label="MAE">{{ metrics.mae }}</el-descriptions-item>
      <el-descriptions-item label="RMSE">{{ metrics.rmse }}</el-descriptions-item>
      <el-descriptions-item label="MAPE">{{ metrics.mape }}%</el-descriptions-item>
      <el-descriptions-item label="评级">
        <el-tag :type="metrics.grade === '优秀' ? 'success' : metrics.grade === '良好' ? 'warning' : 'info'">
          {{ metrics.grade }}
        </el-tag>
      </el-descriptions-item>
    </el-descriptions>
    <el-empty v-else description="点击「开始预测」后显示精度指标" :image-size="80" />

    <div class="disclaimer">预测仅供参考，不构成投资建议</div>
  </el-card>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import ChartCard from '../components/ChartCard.vue'
import { predictArima, predictArimax } from '../api/predict'
import { getRegions, getCategories } from '../api/auth'

const categoryId = ref(1)
const regionId = ref(1)
const model = ref('arimax')
const days = ref(30)
const loading = ref(false)
const history = ref([])
const forecast = ref([])
const metrics = ref(null)
const regions = ref([])
const categories = ref([])

const livestockCategories = computed(() => categories.value.filter((c) => c.type === 'livestock'))

const option = computed(() => {
  const histLine = history.value.map((p) => [p.date, p.value])
  const fcLine = forecast.value.map((p) => [p.date, p.value])
  // 衔接点：预测线从历史最后一点开始
  if (history.value.length && forecast.value.length) {
    fcLine.unshift([history.value[history.value.length - 1].date,
                    history.value[history.value.length - 1].value])
  }
  // 置信带：lower 作 stack 基底（透明），(upper-lower) 为带厚（浅橙填充）
  const lowerBase = forecast.value.map((p) => [p.date, p.lower])
  const bandDepth = forecast.value.map(
    (p) => [p.date, p.lower == null || p.upper == null ? null
            : Number((p.upper - p.lower).toFixed(4))])
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['历史价格', '预测价格'] },
    xAxis: { type: 'time' },
    yAxis: { type: 'value', name: '元/斤', scale: true },
    series: [
      { name: '历史价格', type: 'line', data: histLine, showSymbol: false,
        itemStyle: { color: '#409eff' },
        lineStyle: { width: 2 } },
      { name: '预测价格', type: 'line', data: fcLine, showSymbol: false,
        itemStyle: { color: '#e6a23c' },
        lineStyle: { width: 2, type: 'dashed' } },
      { name: 'ci_base', type: 'line', data: lowerBase, stack: 'ci',
        symbol: 'none', lineStyle: { opacity: 0 }, silent: true,
        areaStyle: { color: 'transparent' }, tooltip: { show: false } },
      { name: '95%置信区间', type: 'line', data: bandDepth, stack: 'ci',
        symbol: 'none', lineStyle: { opacity: 0 }, silent: true,
        areaStyle: { color: 'rgba(230,162,60,0.18)' } },
    ],
    grid: { left: 50, right: 20, top: 40, bottom: 40 },
  }
})

async function runPredict() {
  loading.value = true
  try {
    const params = { category_id: categoryId.value, region_id: regionId.value, days: days.value }
    const data = model.value === 'arimax'
      ? await predictArimax(params)
      : await predictArima(params)
    history.value = data.history || []
    forecast.value = data.forecast || []
    metrics.value = data.metrics || null
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  regions.value = await getRegions()
  categories.value = await getCategories()
})
</script>

<style scoped>
.metric-bar { display: flex; align-items: center; gap: 12px; margin: 8px 0; font-size: 14px; }
.disclaimer { text-align: center; color: #c0c4cc; font-size: 12px; margin-top: 12px; }
</style>
