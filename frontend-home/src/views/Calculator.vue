<template>
  <div>
    <van-nav-bar title="成本计算器" />

    <van-cell-group inset title="基本信息">
      <van-field v-model="form.category" is-link readonly label="类别"
                 :placeholder="form.category === 'cattle' ? '牛' : '羊'"
                 @click="showPicker = true" />
      <van-field v-model.number="form.weight" type="number" label="体重（kg）" placeholder="如 500" />
      <van-field v-model.number="form.current_price" type="number" label="当前价（元/斤）"
                 placeholder="如 14.5" />
      <van-field v-model.number="form.total_cost" type="number" label="累计成本（元/头）"
                 placeholder="含购入+饲料+其他" />
      <van-field v-model.number="form.predicted_price" type="number" label="预测价（元/斤）"
                 placeholder="30天后预测价" />
    </van-cell-group>

    <div class="btn">
      <van-button round block type="primary" :loading="loading" @click="calculate">算一算</van-button>
    </div>

    <!-- 计算结果 -->
    <template v-if="result">
      <van-cell-group inset title="现在出栏">
        <van-cell title="卖价收入" :value="`${result.revenue} 元`" />
        <van-cell title="净利润" :value="`${result.profit} 元`"
                  :value-class="result.profit >= 0 ? 'green' : 'red'" />
        <van-cell title="盈亏平衡价" :value="`${result.breakeven_price} 元/斤`" />
        <van-cell title="每天喂养成本" :value="`${result.daily_total_cost} 元/天`" />
      </van-cell-group>

      <van-cell-group inset title="再养30天（压栏）" style="margin-top: 12px" v-if="delay">
        <van-cell title="30天后体重" :value="`${delay.future_weight} kg`" />
        <van-cell title="新增成本" :value="`${delay.future_extra_cost} 元`" />
        <van-cell title="压栏多卖" :value="`${delay.diff} 元`"
                  :value-class="delay.diff >= 0 ? 'green' : 'red'" />
        <van-cell title="结论" :value="delay.better ? '压栏更划算' : '现在卖更划算'" />
      </van-cell-group>
    </template>

    <van-popup v-model:show="showPicker" position="bottom" round>
      <van-picker :columns="pickerColumns" @confirm="onPick" @cancel="showPicker = false" />
    </van-popup>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { showToast } from 'vant'
import { calcProfit, calcDelay } from '../api/cost'

const showPicker = ref(false)
const loading = ref(false)
const result = ref(null)
const delay = ref(null)
const pickerColumns = [
  { text: '牛', value: 'cattle' },
  { text: '羊', value: 'sheep' },
]

const form = reactive({
  category: 'cattle',
  weight: 500,
  current_price: 14.5,
  total_cost: 12000,
  predicted_price: 14.0,
})

function onPick({ selectedValues }) {
  form.category = (selectedValues && selectedValues[0]) || 'cattle'
  showPicker.value = false
}

async function calculate() {
  if (!form.weight || !form.current_price || !form.total_cost) {
    showToast('请填写体重、当前价、累计成本')
    return
  }
  loading.value = true
  try {
    result.value = await calcProfit(form)
    if (form.predicted_price) {
      delay.value = await calcDelay({ ...form, days: 30 })
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.btn { margin: 20px 16px; }
:deep(.green) { color: #07c160; }
:deep(.red) { color: #ee0a24; }
</style>
