<template>
  <div>
    <!-- 四种饲料最新价卡片 -->
    <el-row :gutter="16">
      <el-col :span="6" v-for="f in latest" :key="f.category_id">
        <el-card shadow="hover" class="feed-card">
          <div class="name">{{ f.feed_name }}</div>
          <div class="price">{{ f.price }} <small>元/斤</small></div>
          <div class="meta">{{ f.price_per_kg }} 元/kg · {{ f.record_date }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 趋势图 -->
    <el-card shadow="never" style="margin-top: 16px">
      <el-form inline>
        <el-form-item label="饲料">
          <el-select v-model="feedName" style="width: 120px" @change="loadTrend">
            <el-option v-for="f in latest" :key="f.category_id" :label="f.feed_name" :value="f.feed_name" />
          </el-select>
        </el-form-item>
        <el-form-item label="地区">
          <el-select v-model="regionId" style="width: 140px" @change="loadTrend">
            <el-option v-for="r in regions" :key="r.id" :label="r.name" :value="r.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <ChartCard title="饲料价格趋势" :option="option" :height="360" />
    </el-card>

    <!-- 明细表 -->
    <el-card shadow="never" style="margin-top: 16px">
      <template #header>饲料价格明细</template>
      <el-table :data="rows" stripe border v-loading="loading">
        <el-table-column prop="record_date" label="日期" width="120" />
        <el-table-column prop="feed_name" label="饲料" width="100" />
        <el-table-column prop="region_name" label="地区" width="110" />
        <el-table-column prop="price" label="价格（元/斤）" width="130" />
        <el-table-column prop="source" label="来源" width="100" />
      </el-table>
      <el-pagination class="pager" layout="total, prev, pager, next"
                     :total="total" v-model:current-page="page" :page-size="20"
                     @change="loadList" />
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import ChartCard from '../components/ChartCard.vue'
import { getLatestFeed, getFeedTrend, getFeedList } from '../api/feed'
import { getRegions } from '../api/auth'

const latest = ref([])
const feedName = ref('玉米')
const regionId = ref(1)
const trend = ref([])
const rows = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const regions = ref([])

const option = computed(() => ({
  tooltip: { trigger: 'axis' },
  xAxis: { type: 'category', data: trend.value.map((p) => p.date) },
  yAxis: { type: 'value', name: '元/斤', scale: true },
  series: [{ type: 'line', smooth: true, data: trend.value.map((p) => p.price),
             areaStyle: { opacity: 0.15 } }],
  grid: { left: 50, right: 20, top: 30, bottom: 30 },
}))

async function loadTrend() {
  if (!feedName.value) return
  trend.value = await getFeedTrend({ feed_name: feedName.value, region_id: regionId.value })
}

async function loadList() {
  loading.value = true
  try {
    const data = await getFeedList({ page: page.value, page_size: 20 })
    rows.value = data.list
    total.value = data.total
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  regions.value = await getRegions()
  latest.value = await getLatestFeed({ region_id: 1 })
  if (latest.value.length) feedName.value = latest.value[0].feed_name
  loadTrend()
  loadList()
})
</script>

<style scoped>
.feed-card { text-align: center; }
.name { color: #909399; }
.price { font-size: 26px; font-weight: bold; color: #e6a23c; margin: 6px 0; }
.price small { font-size: 12px; color: #909399; }
.meta { color: #c0c4cc; font-size: 12px; }
.pager { margin-top: 12px; justify-content: flex-end; }
</style>
