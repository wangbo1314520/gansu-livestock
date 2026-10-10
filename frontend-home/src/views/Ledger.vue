<template>
  <div>
    <van-nav-bar title="家庭账本" left-arrow @click-left="$router.back()">
      <template #right><span @click="showAdd = true">＋记账</span></template>
    </van-nav-bar>

    <!-- 年度汇总 -->
    <div class="summary" v-if="summaryData">
      <div class="s-item"><div class="s-num green">+{{ summaryData.total_income }}</div>
        <div class="s-label">收入（元）</div></div>
      <div class="s-item"><div class="s-num red">-{{ summaryData.total_expense }}</div>
        <div class="s-label">支出（元）</div></div>
      <div class="s-item"><div class="s-num" :class="summaryData.net_profit >= 0 ? 'green' : 'red'">
        {{ summaryData.net_profit }}</div><div class="s-label">净收益（元）</div></div>
    </div>

    <!-- 账目列表 -->
    <van-list v-model:loading="loading" :finished="finished" @load="load">
      <van-swipe-cell v-for="r in records" :key="r.id">
        <van-cell :title="r.category" :label="`${r.trade_date} ${r.counterparty || ''}`">
          <template #value>
            <span :class="r.type === 'income' ? 'green' : 'red'">
              {{ r.type === 'income' ? '+' : '-' }}{{ r.amount }}
            </span>
          </template>
        </van-cell>
        <template #right>
          <van-button square type="danger" text="删除" @click="remove(r)" />
        </template>
      </van-swipe-cell>
      <van-empty v-if="!records.length && !loading" description="记一笔卖牛卖羊的收入吧" />
    </van-list>

    <!-- 记账弹层 -->
    <van-popup v-model:show="showAdd" position="bottom" round>
      <van-form @submit="submitAdd" style="padding: 16px 4px">
        <van-picker :columns="typeColumns" title="类型"
                    @confirm="(e) => (newItem.type = e.selectedValues[0])" />
        <van-field v-model="newItem.category" label="分类" placeholder="卖牛 / 卖羊 / 购饲料" />
        <van-field v-model.number="newItem.amount" type="number" label="金额（元）" />
        <van-field v-model="newItem.trade_date" label="日期" type="date" />
        <van-field v-model="newItem.counterparty" label="交易对方" placeholder="选填" />
        <div style="margin: 12px 16px">
          <van-button round block type="primary" native-type="submit">保存</van-button>
        </div>
      </van-form>
    </van-popup>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { showConfirmDialog, showToast } from 'vant'
import { getLedgerList, addLedger, deleteLedger, getLedgerSummary } from '../api/ledger'

const FARM_ID = Number(localStorage.getItem('farmId') || 1)

const records = ref([])
const summaryData = ref(null)
const loading = ref(false)
const finished = ref(false)
const showAdd = ref(false)
const typeColumns = [{ text: '收入', value: 'income' }, { text: '支出', value: 'expense' }]
const newItem = reactive({
  type: 'income', category: '卖牛', amount: null,
  trade_date: new Date().toISOString().slice(0, 10), counterparty: '',
})

async function load() {
  loading.value = true
  try {
    const data = await getLedgerList({ farm_id: FARM_ID, page: 1, page_size: 50 })
    records.value = data.list
    finished.value = true
    summaryData.value = await getLedgerSummary({ farm_id: FARM_ID })
  } finally {
    loading.value = false
  }
}

async function submitAdd() {
  if (!newItem.amount) {
    showToast('请填写金额')
    return
  }
  await addLedger({ ...newItem, farm_id: FARM_ID })
  showToast('记账成功')
  showAdd.value = false
  Object.assign(newItem, { type: 'income', category: '卖牛', amount: null,
                           counterparty: '' })
  load()
}

async function remove(r) {
  await showConfirmDialog({ title: '删除', message: '确定删除这条账目？' })
  await deleteLedger(r.id, FARM_ID)
  showToast('已删除')
  load()
}

onMounted(load)
</script>

<style scoped>
.summary { display: flex; background: #fff; padding: 14px 0; margin-bottom: 8px; }
.s-item { flex: 1; text-align: center; }
.s-num { font-size: 20px; font-weight: bold; }
.s-label { color: #969799; font-size: 12px; margin-top: 2px; }
.green { color: #07c160; }
.red { color: #ee0a24; }
</style>
