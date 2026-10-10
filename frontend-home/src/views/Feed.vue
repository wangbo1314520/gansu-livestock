<template>
  <div>
    <van-nav-bar title="饲料库存" left-arrow @click-left="$router.back()">
      <template #right><span @click="showIn = true">＋入库</span></template>
    </van-nav-bar>

    <!-- 库存卡片 -->
    <div class="stock-list">
      <van-card v-for="s in stocks" :key="s.id">
        <template #title>
          <span class="f-name">{{ s.feed_name }}</span>
          <van-tag type="danger" v-if="s.warning">库存不足</van-tag>
        </template>
        <template #desc>
          <div class="f-qty">{{ s.quantity }} {{ s.unit }}</div>
          <div class="f-meta" v-if="s.unit_price">最近入库 {{ s.unit_price }} 元/kg</div>
          <div class="f-meta" v-if="s.warn_threshold">预警线 {{ s.warn_threshold }} {{ s.unit }}</div>
        </template>
        <template #footer>
          <van-button size="small" plain type="primary" @click="openOut(s)">出库</van-button>
        </template>
      </van-card>
      <van-empty v-if="!stocks.length" description="暂无库存记录" />
    </div>

    <!-- 入库弹层 -->
    <van-popup v-model:show="showIn" position="bottom" round>
      <van-form @submit="submitIn" style="padding: 16px 4px">
        <van-picker :columns="feedColumns" title="饲料"
                    @confirm="(e) => (inForm.feed_name = e.selectedOptions[0].text)" />
        <van-field v-model.number="inForm.quantity" type="number" label="数量（kg）" />
        <van-field v-model.number="inForm.unit_price" type="number" label="单价（元/kg）" />
        <van-field v-model="inForm.supplier" label="供应商" placeholder="选填" />
        <div style="margin: 12px 16px">
          <van-button round block type="primary" native-type="submit">入库</van-button>
        </div>
      </van-form>
    </van-popup>

    <!-- 出库弹层 -->
    <van-dialog v-model:show="showOut" title="饲料出库（喂养）" show-cancel-button
                @confirm="submitOut">
      <van-field v-model.number="outForm.quantity" type="number" label="数量（kg）"
                 placeholder="今天喂了多少" style="padding: 16px 0" />
    </van-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { showToast } from 'vant'
import { getFeedStock, feedIn, feedOut } from '../api/farm'

const FARM_ID = Number(localStorage.getItem('farmId') || 1)

const stocks = ref([])
const showIn = ref(false)
const showOut = ref(false)
const feedColumns = ['玉米', '豆粕', '麸皮', '苜蓿草'].map((t) => ({ text: t, value: t }))
const inForm = reactive({ feed_name: '玉米', quantity: null, unit_price: null, supplier: '' })
const outForm = reactive({ feed_name: '', quantity: null })

async function load() {
  stocks.value = await getFeedStock({ farm_id: FARM_ID })
}

async function submitIn() {
  if (!inForm.quantity) {
    showToast('请填写数量')
    return
  }
  await feedIn({ ...inForm, farm_id: FARM_ID })
  showToast('入库成功')
  showIn.value = false
  Object.assign(inForm, { feed_name: '玉米', quantity: null, unit_price: null, supplier: '' })
  load()
}

function openOut(s) {
  outForm.feed_name = s.feed_name
  outForm.quantity = null
  showOut.value = true
}

async function submitOut() {
  if (!outForm.quantity) {
    showToast('请填写数量')
    return
  }
  try {
    await feedOut({ ...outForm, farm_id: FARM_ID })
    showToast('出库成功')
    load()
  } catch (e) {
    /* 库存不足等错误由拦截器 toast */
  }
}

onMounted(load)
</script>

<style scoped>
.stock-list { margin: 8px; }
.f-name { font-size: 16px; font-weight: bold; margin-right: 8px; }
.f-qty { font-size: 20px; color: #323233; margin: 4px 0; }
.f-meta { color: #969799; font-size: 12px; }
</style>
