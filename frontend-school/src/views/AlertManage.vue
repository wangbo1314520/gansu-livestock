<template>
  <div>
    <!-- 规则管理 -->
    <el-card shadow="never">
      <template #header>
        <div class="card-head">
          <span>预警规则</span>
          <el-button type="primary" size="small" @click="dialogVisible = true">新增规则</el-button>
        </div>
      </template>
      <el-table :data="rules" stripe border>
        <el-table-column prop="name" label="规则名称" min-width="160" />
        <el-table-column label="类型" width="120">
          <template #default="{ row }">{{ typeText(row.rule_type) }}</template>
        </el-table-column>
        <el-table-column prop="threshold" label="阈值（元/斤）" width="130" />
        <el-table-column prop="continuous_days" label="连续天数" width="100" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'info'">
              {{ row.enabled ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button link type="primary" @click="toggleRule(row)">
              {{ row.enabled ? '停用' : '启用' }}
            </el-button>
            <el-button link type="danger" @click="removeRule(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 预警记录 -->
    <el-card shadow="never" style="margin-top: 16px">
      <template #header>预警记录</template>
      <el-table :data="records" stripe border>
        <el-table-column prop="trigger_time" label="触发时间" width="170" />
        <el-table-column prop="message" label="预警内容" min-width="300" show-overflow-tooltip />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.is_read ? 'info' : 'danger'">
              {{ row.is_read ? '已读' : '未读' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="90">
          <template #default="{ row }">
            <el-button v-if="!row.is_read" link type="primary" @click="read(row)">标记已读</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination class="pager" layout="total, prev, pager, next"
                     :total="recordTotal" v-model:current-page="recordPage" :page-size="20"
                     @change="loadRecords" />
    </el-card>

    <!-- 新增规则对话框 -->
    <el-dialog v-model="dialogVisible" title="新增预警规则" width="480px">
      <el-form :model="newRule" label-width="100px">
        <el-form-item label="规则名称">
          <el-input v-model="newRule.name" placeholder="如：活牛跌破成本线" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="newRule.category_id">
            <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="规则类型">
          <el-select v-model="newRule.rule_type">
            <el-option label="跌破成本线" value="below_cost" />
            <el-option label="高于阈值" value="above_price" />
            <el-option label="连续上涨" value="continuous_rise" />
            <el-option label="连续下跌" value="continuous_fall" />
            <el-option label="饲料涨价" value="feed_rise" />
          </el-select>
        </el-form-item>
        <el-form-item label="阈值（元/斤）">
          <el-input-number v-model="newRule.threshold" :min="0" :step="0.5" />
        </el-form-item>
        <el-form-item label="连续天数">
          <el-input-number v-model="newRule.continuous_days" :min="2" :max="15" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="createRule">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getRules, addRule, updateRule, deleteRule, getRecords, markRead } from '../api/alert'
import { getCategories } from '../api/auth'

const TYPE_CN = {
  below_cost: '跌破成本线', above_price: '高于阈值',
  continuous_rise: '连续上涨', continuous_fall: '连续下跌', feed_rise: '饲料涨价',
}

const rules = ref([])
const records = ref([])
const recordTotal = ref(0)
const recordPage = ref(1)
const categories = ref([])
const dialogVisible = ref(false)
const newRule = reactive({
  name: '', category_id: 1, rule_type: 'below_cost',
  threshold: 13, continuous_days: 3,
})

const typeText = (t) => TYPE_CN[t] || t

async function loadRules() {
  rules.value = await getRules()
}

async function loadRecords() {
  const data = await getRecords({ page: recordPage.value, page_size: 20 })
  records.value = data.list
  recordTotal.value = data.total
}

async function createRule() {
  if (!newRule.name) {
    ElMessage.warning('请填写规则名称')
    return
  }
  await addRule({ ...newRule })
  ElMessage.success('规则已创建')
  dialogVisible.value = false
  loadRules()
}

async function toggleRule(row) {
  await updateRule({ id: row.id, enabled: row.enabled ? 0 : 1 })
  loadRules()
}

async function removeRule(row) {
  await ElMessageBox.confirm(`确定删除规则「${row.name}」？`, '提示', { type: 'warning' })
  await deleteRule(row.id)
  ElMessage.success('已删除')
  loadRules()
}

async function read(row) {
  await markRead(row.id)
  loadRecords()
}

onMounted(async () => {
  categories.value = await getCategories()
  loadRules()
  loadRecords()
})
</script>

<style scoped>
.card-head { display: flex; justify-content: space-between; align-items: center; }
.pager { margin-top: 12px; justify-content: flex-end; }
</style>
