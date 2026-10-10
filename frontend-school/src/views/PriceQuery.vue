<template>
  <el-card shadow="never">
    <!-- 筛选区 -->
    <el-form inline :model="query">
      <el-form-item label="地区">
        <el-select v-model="query.region_id" placeholder="全部" clearable style="width: 140px">
          <el-option v-for="r in regions" :key="r.id" :label="r.name" :value="r.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="分类">
        <el-select v-model="query.category_id" placeholder="全部" clearable style="width: 120px">
          <el-option v-for="c in livestockCategories" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="品种">
        <el-select v-model="query.breed_id" placeholder="全部" clearable style="width: 140px">
          <el-option v-for="b in breeds" :key="b.id" :label="b.name" :value="b.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="日期">
        <el-date-picker v-model="dateRange" type="daterange" value-format="YYYY-MM-DD"
                        start-placeholder="开始" end-placeholder="结束" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="loadData(1)">查询</el-button>
        <el-button @click="exportCsv">导出 CSV</el-button>
      </el-form-item>
    </el-form>

    <!-- 数据表格 -->
    <el-table :data="rows" v-loading="loading" stripe border>
      <el-table-column prop="record_date" label="日期" width="110" />
      <el-table-column prop="region_name" label="地区" width="100" />
      <el-table-column prop="category_name" label="分类" width="80" />
      <el-table-column prop="breed_name" label="品种" width="110" />
      <el-table-column prop="price" label="价格（元/斤）" width="120" />
      <el-table-column prop="source" label="来源" width="90" />
      <el-table-column prop="source_detail" label="来源明细" min-width="180" show-overflow-tooltip />
    </el-table>

    <el-pagination class="pager" layout="total, prev, pager, next, sizes"
                   :total="total" v-model:current-page="query.page"
                   v-model:page-size="query.page_size"
                   :page-sizes="[20, 50, 100]" @change="loadData()" />
  </el-card>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { getPriceList } from '../api/price'
import { getRegions, getBreeds, getCategories } from '../api/auth'

const query = reactive({
  region_id: null, category_id: null, breed_id: null,
  page: 1, page_size: 20,
})
const dateRange = ref([])
const rows = ref([])
const total = ref(0)
const loading = ref(false)
const regions = ref([])
const breeds = ref([])
const categories = ref([])

const livestockCategories = computed(() => categories.value.filter((c) => c.type === 'livestock'))

async function loadData(page) {
  if (page) query.page = page
  loading.value = true
  try {
    const params = { ...query }
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    const data = await getPriceList(params)
    rows.value = data.list
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function exportCsv() {
  // 后端导出接口直接下载
  const params = new URLSearchParams()
  if (query.region_id) params.set('region_id', query.region_id)
  if (query.category_id) params.set('category_id', query.category_id)
  if (dateRange.value && dateRange.value.length === 2) {
    params.set('start_date', dateRange.value[0])
    params.set('end_date', dateRange.value[1])
  }
  window.open(`/api/price/export?${params.toString()}`)
}

onMounted(async () => {
  regions.value = await getRegions()
  breeds.value = await getBreeds()
  categories.value = await getCategories()
  loadData(1)
})
</script>

<style scoped>
.pager { margin-top: 16px; justify-content: flex-end; }
</style>
