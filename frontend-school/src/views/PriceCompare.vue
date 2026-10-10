<template>
  <el-card shadow="never">
    <el-form inline>
      <el-form-item label="分类">
        <el-select v-model="categoryId" style="width: 120px">
          <el-option v-for="c in livestockCategories" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="对比地区（可多选）">
        <el-select v-model="selectedRegions" multiple collapse-tags style="min-width: 320px">
          <el-option v-for="r in cityRegions" :key="r.id" :label="r.name" :value="r.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="范围">
        <el-radio-group v-model="range">
          <el-radio-button value="30">近1月</el-radio-button>
          <el-radio-button value="90">近3月</el-radio-button>
          <el-radio-button value="365">近一年</el-radio-button>
        </el-radio-group>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="load">对比</el-button>
      </el-form-item>
    </el-form>

    <ChartCard title="各市州均价对比" :option="option" :height="420" />
  </el-card>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import ChartCard from '../components/ChartCard.vue'
import { getPriceCompare } from '../api/price'
import { getRegions, getCategories } from '../api/auth'

const categoryId = ref(1)
const selectedRegions = ref([2, 9, 11])     // 默认兰州、平凉、庆阳（牛羊主产区）
const range = ref('90')
const compareData = ref([])
const regions = ref([])
const categories = ref([])

const livestockCategories = computed(() => categories.value.filter((c) => c.type === 'livestock'))
const cityRegions = computed(() => regions.value.filter((r) => r.level === 2))

const option = computed(() => ({
  tooltip: { trigger: 'axis' },
  xAxis: { type: 'category', data: compareData.value.map((d) => d.region_name),
           axisLabel: { rotate: 30 } },
  yAxis: { type: 'value', name: '均价（元/斤）', scale: true },
  series: [{
    type: 'bar',
    data: compareData.value.map((d) => d.avg_price),
    label: { show: true, position: 'top' },
    itemStyle: { color: '#409eff' },
  }],
  grid: { left: 50, right: 20, top: 30, bottom: 60 },
}))

async function load() {
  if (!selectedRegions.value.length) return
  const startDate = new Date(Date.now() - Number(range.value) * 86400000).toISOString().slice(0, 10)
  compareData.value = await getPriceCompare({
    category_id: categoryId.value,
    region_ids: selectedRegions.value.join(','),
    start_date: startDate,
  })
}

onMounted(async () => {
  regions.value = await getRegions()
  categories.value = await getCategories()
  load()
})
</script>
