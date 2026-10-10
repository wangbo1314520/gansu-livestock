<template>
  <div>
    <van-nav-bar title="存栏记录" left-arrow @click-left="$router.back()">
      <template #right><span @click="showAdd = true">＋新增</span></template>
    </van-nav-bar>

    <!-- 统计 -->
    <van-grid :column-num="2" :border="false">
      <van-grid-item><div class="s-num">{{ stats.cattle }}</div><div class="s-label">牛（在养）</div></van-grid-item>
      <van-grid-item><div class="s-num">{{ stats.sheep }}</div><div class="s-label">羊（在养）</div></van-grid-item>
    </van-grid>

    <!-- 存栏列表 -->
    <van-list v-model:loading="loading" :finished="finished" @load="load">
      <van-swipe-cell v-for="l in list" :key="l.id">
        <van-cell :title="`${l.category === 'cattle' ? '牛' : '羊'} ${l.ear_tag || l.id}号`"
                  :label="`${l.weight || '?'} kg · ${statusText(l.status)}`"
                  is-link @click="showEdit(l)" />
        <template #right>
          <van-button square type="danger" text="删除" @click="remove(l)" />
        </template>
      </van-swipe-cell>
      <van-empty v-if="!list.length && !loading" description="还没有记录，点右上角新增" />
    </van-list>

    <!-- 新增弹层 -->
    <van-popup v-model:show="showAdd" position="bottom" round>
      <van-form @submit="submitAdd" style="padding: 16px 4px">
        <van-picker :columns="pickerColumns" @confirm="(e) => (newItem.category = e.selectedValues[0])" />
        <van-field v-model="newItem.ear_tag" label="耳标号" placeholder="选填" />
        <van-field v-model.number="newItem.weight" type="number" label="体重（kg）" />
        <van-field v-model.number="newItem.purchase_price" type="number" label="购入价（元）" />
        <div style="margin: 12px 16px">
          <van-button round block type="primary" native-type="submit">保存</van-button>
        </div>
      </van-form>
    </van-popup>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { showConfirmDialog, showToast } from 'vant'
import { getLivestock, addLivestock, deleteLivestock } from '../api/farm'

const FARM_ID = Number(localStorage.getItem('farmId') || 1)   // 家用版单牧场

const list = ref([])
const loading = ref(false)
const finished = ref(false)
const showAdd = ref(false)
const pickerColumns = [{ text: '牛', value: 'cattle' }, { text: '羊', value: 'sheep' }]
const newItem = reactive({ category: 'cattle', ear_tag: '', weight: null, purchase_price: null })

const stats = computed(() => {
  const raising = list.value.filter((l) => l.status === 'raising')
  return {
    cattle: raising.filter((l) => l.category === 'cattle').length,
    sheep: raising.filter((l) => l.category === 'sheep').length,
  }
})

const statusText = (s) => ({ raising: '在养', sold: '已出栏', dead: '死亡' }[s] || s)

async function load() {
  loading.value = true
  try {
    const data = await getLivestock({ farm_id: FARM_ID, status: '' })
    list.value = data.list
    finished.value = true
  } finally {
    loading.value = false
  }
}

async function submitAdd() {
  await addLivestock({ ...newItem, farm_id: FARM_ID })
  showToast('已添加')
  showAdd.value = false
  Object.assign(newItem, { category: 'cattle', ear_tag: '', weight: null, purchase_price: null })
  load()
}

async function remove(l) {
  await showConfirmDialog({ title: '删除', message: `确定删除 ${l.ear_tag || l.id}号 记录？` })
  await deleteLivestock(l.id, FARM_ID)
  showToast('已删除')
  load()
}

function showEdit(l) {
  // TODO: 编辑弹层（体重更新最常用，联调阶段补全）
  showToast('左滑可删除，编辑功能开发中')
}

onMounted(load)
</script>

<style scoped>
.s-num { font-size: 28px; font-weight: bold; color: #1989fa; }
.s-label { color: #969799; font-size: 12px; }
</style>
