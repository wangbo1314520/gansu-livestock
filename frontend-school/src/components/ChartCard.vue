<template>
  <el-card class="chart-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <span>{{ title }}</span>
        <slot name="extra" />
      </div>
    </template>
    <div ref="chartRef" class="chart" :style="{ height: height + 'px' }" />
  </el-card>
</template>

<script setup>
// ECharts 通用容器：传入 option 自动渲染 + 窗口自适应
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  title: { type: String, default: '' },
  option: { type: Object, required: true },
  height: { type: Number, default: 360 },
})

const chartRef = ref(null)
let chart = null

function render() {
  if (!chartRef.value) return
  if (!chart) {
    chart = echarts.init(chartRef.value)
  }
  chart.setOption(props.option, true)
}

function resize() {
  chart && chart.resize()
}

onMounted(() => {
  render()
  window.addEventListener('resize', resize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  chart && chart.dispose()
})

watch(() => props.option, render, { deep: true })
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.chart { width: 100%; }
</style>
