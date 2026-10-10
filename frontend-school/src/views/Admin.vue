<template>
  <div>
    <!-- 用户管理 -->
    <el-card shadow="never">
      <template #header>
        <div class="card-head">
          <span>用户管理</span>
          <el-button type="primary" size="small" @click="userDialog = true">新增用户</el-button>
        </div>
      </template>
      <el-table :data="users" stripe border>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="用户名" width="140" />
        <el-table-column prop="real_name" label="姓名" width="120" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : row.role === 'editor' ? 'warning' : 'info'">
              {{ row.role }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_login" label="最后登录" width="170" />
        <el-table-column prop="created_at" label="创建时间" width="170" />
      </el-table>
    </el-card>

    <!-- 爬虫与系统 -->
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>爬虫管理</template>
          <el-space>
            <el-button type="primary" @click="run('gov')">抓政府价格</el-button>
            <el-button type="warning" @click="run('feed')">抓饲料价格</el-button>
            <el-button @click="loadLog">刷新日志</el-button>
          </el-space>
          <pre class="spider-log">{{ logText }}</pre>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>系统信息</template>
          <el-descriptions :column="1" border v-if="sysInfo">
            <el-descriptions-item label="Python">{{ sysInfo.python }}</el-descriptions-item>
            <el-descriptions-item label="Flask">{{ sysInfo.flask }}</el-descriptions-item>
            <el-descriptions-item label="SQLAlchemy">{{ sysInfo.sqlalchemy }}</el-descriptions-item>
            <el-descriptions-item label="pandas">{{ sysInfo.libs.pandas }}</el-descriptions-item>
            <el-descriptions-item label="statsmodels">{{ sysInfo.libs.statsmodels }}</el-descriptions-item>
            <el-descriptions-item label="scikit-learn">{{ sysInfo.libs['scikit-learn'] }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>

    <!-- 新增用户 -->
    <el-dialog v-model="userDialog" title="新增用户" width="440px">
      <el-form :model="newUser" label-width="80px">
        <el-form-item label="用户名"><el-input v-model="newUser.username" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="newUser.password" show-password /></el-form-item>
        <el-form-item label="姓名"><el-input v-model="newUser.real_name" /></el-form-item>
        <el-form-item label="角色">
          <el-select v-model="newUser.role">
            <el-option label="管理员" value="admin" />
            <el-option label="录入员" value="editor" />
            <el-option label="只读" value="viewer" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="userDialog = false">取消</el-button>
        <el-button type="primary" @click="createUser">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getUsers, addUser, runSpider, getSpiderLog, getSystemInfo } from '../api/admin'

const users = ref([])
const logText = ref('（暂无日志）')
const sysInfo = ref(null)
const userDialog = ref(false)
const newUser = reactive({ username: '', password: '', real_name: '', role: 'viewer' })

async function loadUsers() {
  const data = await getUsers({ page: 1, page_size: 50 })
  users.value = data.list
}

async function createUser() {
  if (!newUser.username || !newUser.password) {
    ElMessage.warning('用户名和密码必填')
    return
  }
  await addUser({ ...newUser })
  ElMessage.success('用户已创建')
  userDialog.value = false
  loadUsers()
}

async function run(which) {
  await runSpider(which)
  ElMessage.success('任务已提交')
}

async function loadLog() {
  const data = await getSpiderLog({ tail: 50 })
  logText.value = data.exists ? data.lines.join('\n') : '（暂无日志）'
}

onMounted(() => {
  loadUsers()
  getSystemInfo().then((d) => { sysInfo.value = d })
})
</script>

<style scoped>
.card-head { display: flex; justify-content: space-between; align-items: center; }
.spider-log {
  margin-top: 12px; background: #1e1e1e; color: #d4d4d4;
  padding: 12px; border-radius: 4px; height: 220px; overflow: auto;
  font-size: 12px; white-space: pre-wrap;
}
</style>
