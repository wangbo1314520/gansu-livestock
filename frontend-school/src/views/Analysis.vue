<template>
  <div>
    <el-card shadow="never">
      <el-form inline>
        <el-form-item label="地区">
          <el-select v-model="regionId" style="width: 140px" @change="loadMatrix">
            <el-option v-for="r in regions" :key="r.id" :label="r.name" :value="r.id" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="loadMatrix">重新计算</el-button>
        </el-form-item>
      </el-form>

      <!-- 相关性热力图：牲畜分类 x 饲料分类 -->
      <ChartCard title="饲料价格与牛羊价格相关性（皮尔逊系数）" :option="heatmapOption"
                 :height="380" />
    </el-card>

    <el-card shadow="never" style="margin-top: 16px">
      <template #header>
        相关性明细与最优滞后（饲料价先行天数）
      </template>
      <el-table :data="details" stripe border>
        <el-table-column prop="livestock" label="牲畜分类" width="120" />
        <el-table-column prop="feed" label="饲料" width="120" />
        <el-table-column prop="correlation" label="相关系数" width="120" />
        <el-table-column prop="best_lag_days" label="最优滞后（天）" width="140" />
        <el-table-column label="强度">
          <template #default="{ row }">
            <el-tag :type="strength(row.correlation).type">
              {{ strength(row.correlation).label }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import ChartCard from '../components/ChartCard.vue'
import { getCorrelation } from '../api/analysis'
import { getRegions } from '../api/auth'

const regionId = ref(1)
const loading = ref(false)
const matrix = ref([])
const details = ref([])
const regions = ref([])

const feedNames = computed(() =>
  (matrix.value[0] && matrix.value[0].values ? matrix.value[0].values.map((v) => v.feed_name) : []))

const heatmapOption = computed(() => {
  const data = []
  matrix.value.forEach((row, i) => {
    row.values.forEach((cell, j) => {
      if (cell.correlation !== null && cell.correlation !== undefined) {
        data.push([j, i, cell.correlation])
      }
    })
  })
  return {
    tooltip: { position: 'top' },
    grid: { left: 80, right: 40, top: 20, bottom: 60 },
    xAxis: { type: 'category', data: feedNames.value },
    yAxis: { type: 'category', data: matrix.value.map((r) => r.category_name) },
    visualMap: { min: -1, max: 1, calculable: true, orient: 'horizontal',
                 left: 'center', bottom: 0,
                 inRange: { color: ['#67c23a', '#ffffff', '#f56c6c'] } },
    series: [{
      type: 'heatmap',
      data,
      label: { show: true, formatter: (p) => p.data[2].toFixed(2) },
    }],
  }
})

function strength(c) {
  const a = Math.abs(c || 0)
  if (a >= 0.7) return { label: '强相关', type: 'danger' }
  if (a >= 0.4) return { label: '中等相关', type: 'warning' }
  return { label: '弱相关', type: 'info' }
}

async function loadMatrix() {
  loading.value = true
  try {
    const data = await getCorrelation({ region_id: regionId.value })
    matrix.value = data.matrix || []
    details.value = data.details || []
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  regions.value = await getRegions()
  loadMatrix()
})
</script>
