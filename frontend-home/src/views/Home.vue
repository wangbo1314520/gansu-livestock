<template>
  <div class="home">
    <van-nav-bar title="今日行情" />

    <!-- 今日价格：活牛 / 活羊 / 玉米 / 豆粕 -->
    <van-grid :column-num="2" :border="false" class="price-grid">
      <van-grid-item v-for="p in todayPrices" :key="p.category_id">
        <div class="p-name">{{ p.category_name || p.feed_name }}</div>
        <div class="p-value">{{ p.price }}<small> 元/斤</small></div>
        <div class="p-date">{{ p.record_date }}</div>
      </van-grid-item>
    </van-grid>

    <!-- 数据来源提示（不显眼） -->
    <div class="src-tip" v-if="dataMode === 'real'">当前显示定西周报数据</div>
    <div class="src-tip" v-else-if="dataMode === 'sample'">当前显示示例数据</div>

    <!-- 预警提醒 -->
    <van-notice-bar left-icon="warning-o" :text="alertText" color="#ed6a0c"
                    background="#fffbe8" v-if="unreadAlerts > 0" />

    <!-- 快捷入口（需求文档 H2） -->
    <van-cell-group inset title="快捷功能">
      <van-cell title="💡 出栏建议" label="现在能不能卖" is-link to="/advice" />
      <van-cell title="🧮 成本计算器" label="算算能赚多少" is-link to="/calculator" />
      <van-cell title="🔔 价格预警" label="跌破成本线提醒" is-link to="/alert"
                :value="unreadAlerts ? `${unreadAlerts}条未读` : ''" />
      <van-cell title="🐄 存栏记录" label="牛羊数量与体重" is-link to="/livestock" />
      <van-cell title="🌾 饲料库存" label="入库出库" is-link to="/feed" />
      <van-cell title="📒 家庭账本" label="收支与利润" is-link to="/ledger" />
    </van-cell-group>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { getLatestPrices } from '../api/price'
import { getLatestFeed } from '../api/feed'
import { getRecords } from '../api/alert'

const latest = ref([])
const feed = ref([])
const unreadAlerts = ref(0)
const dataMode = ref('')   // real=真实周报 sample=示例数据

// 目前只有定西有真实牛羊+饲料周报数据，首页默认取定西
const DEFAULT_REGION_ID = 12

// 先取真实数据（默认排除示例），无数据时回退示例数据并标记
async function loadWithFallback(fetcher, regionId) {
  let data = await fetcher({ region_id: regionId })
  if (Array.isArray(data) && data.length > 0) return { data, sample: false }
  data = await fetcher({ region_id: regionId, include_sample: true })
  return { data: Array.isArray(data) ? data : [], sample: true }
}

// 首页只展示最关心的四项：活牛、活羊、玉米、豆粕
const todayPrices = computed(() => {
  const livestock = latest.value.filter((p) => ['活牛', '活羊'].includes(p.category_name))
  const feeds = feed.value.filter((p) => ['玉米', '豆粕'].includes(p.feed_name))
  return [...livestock, ...feeds]
})

const alertText = computed(() =>
  `您有 ${unreadAlerts.value} 条价格预警未读，点击查看`)

onMounted(async () => {
  try {
    const a = await loadWithFallback(getLatestPrices, DEFAULT_REGION_ID)
    latest.value = a.data
    const b = await loadWithFallback(getLatestFeed, DEFAULT_REGION_ID)
    feed.value = b.data
    dataMode.value = (a.sample || b.sample) ? 'sample' : 'real'
  } catch (e) { /* 后端未起时空展示 */ }
  try {
    const data = await getRecords({ is_read: 0, page: 1, page_size: 1 })
    unreadAlerts.value = data.total
  } catch (e) { /* 同上 */ }
})
</script>

<style scoped>
.price-grid { margin: 8px 0; }
.p-name { color: #646566; font-size: 14px; }
.p-value { font-size: 26px; font-weight: bold; color: #ee0a24; margin: 4px 0; }
.p-value small { font-size: 12px; color: #969799; font-weight: normal; }
.p-date { color: #c8c9cc; font-size: 12px; }
.src-tip { text-align: center; color: #c8c9cc; font-size: 11px; margin: 0 0 4px; }
</style>
