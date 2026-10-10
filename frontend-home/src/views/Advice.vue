<template>
  <div>
    <van-nav-bar title="出栏建议" left-arrow @click-left="$router.back()" />

    <van-cell-group inset title="当前情况">
      <van-field v-model.number="form.weight" type="number" label="体重（kg）" />
      <van-field v-model.number="form.current_price" type="number" label="当前价（元/斤）" />
      <van-field v-model.number="form.total_cost" type="number" label="累计成本（元）" />
      <van-field v-model.number="form.predicted_price" type="number" label="预测价（元/斤）" />
      <div class="btn">
        <van-button round block type="primary" :loading="loading" @click="load">
          给个建议
        </van-button>
      </div>
    </van-cell-group>

    <!-- 建议结果 -->
    <div class="advice-card" v-if="advice">
      <div class="action" :class="actionClass">{{ advice.action_cn }}</div>
      <p class="reason">{{ advice.reason }}</p>
      <van-cell-group inset>
        <van-cell title="成本线" :value="`${advice.cost_line} 元/斤`" />
        <van-cell title="现在卖利润" :value="`${advice.profit_now} 元/头`" />
        <van-cell title="压栏30天差额" :value="`${advice.delay_30d.diff} 元/头`" />
      </van-cell-group>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { showToast } from 'vant'
import { getSellAdvice } from '../api/advice'

const loading = ref(false)
const advice = ref(null)
const form = reactive({
  weight: 500, current_price: 14.5, total_cost: 12000, predicted_price: 14.0,
  region_id: 1,
})

const actionClass = computed(() => ({
  sell: 'sell', hold: 'hold', sell_now: 'sell-now', wait: 'wait',
}[advice.value?.action] || ''))

async function load() {
  if (!form.weight || !form.current_price || !form.total_cost || !form.predicted_price) {
    showToast('请把四项都填上')
    return
  }
  loading.value = true
  try {
    advice.value = await getSellAdvice(form)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.btn { margin: 16px; }
.advice-card { margin: 12px; background: #fff; border-radius: 8px; padding: 20px 16px; }
.action { font-size: 24px; font-weight: bold; text-align: center; margin-bottom: 12px; }
.action.sell { color: #ee0a24; }
.action.sell-now { color: #ee0a24; }
.action.hold { color: #ff976a; }
.action.wait { color: #07c160; }
.reason { color: #646566; line-height: 1.7; font-size: 14px; }
</style>
