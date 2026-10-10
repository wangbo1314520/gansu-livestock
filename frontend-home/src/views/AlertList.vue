<template>
  <div>
    <van-nav-bar title="价格预警" left-arrow @click-left="$router.back()" />

    <van-pull-refresh v-model="refreshing" @refresh="load">
      <van-list v-model:loading="loadingMore" :finished="finished"
                finished-text="没有更多了" @load="loadMore">
        <van-swipe-cell v-for="r in records" :key="r.id">
          <van-cell :title="r.message" :label="r.trigger_time"
                    :class="{ unread: !r.is_read }" @click="read(r)" />
          <template #right>
            <van-button square type="primary" text="已读" @click="read(r)" />
          </template>
        </van-swipe-cell>
      </van-list>
      <van-empty v-if="!records.length && !loadingMore" description="暂无预警，行情平稳" />
    </van-pull-refresh>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { getRecords, markRead } from '../api/alert'

const records = ref([])
const page = ref(1)
const loadingMore = ref(false)
const finished = ref(false)
const refreshing = ref(false)

async function loadMore() {
  loadingMore.value = true
  try {
    const data = await getRecords({ page: page.value, page_size: 20 })
    if (page.value === 1) records.value = []
    records.value.push(...data.list)
    page.value += 1
    if (records.value.length >= data.total) finished.value = true
  } finally {
    loadingMore.value = false
    refreshing.value = false
  }
}

function load() {
  page.value = 1
  finished.value = false
  loadMore()
}

async function read(row) {
  if (row.is_read) return
  await markRead(row.id)
  row.is_read = 1
}
</script>

<style scoped>
.unread :deep(.van-cell__title) { font-weight: bold; }
</style>
