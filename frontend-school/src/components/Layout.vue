<template>
  <el-container class="layout">
    <!-- 侧边菜单（需求文档 9.1 页面清单） -->
    <el-aside width="220px" class="aside">
      <div class="logo">甘肃牛羊价格平台</div>
      <el-menu :default-active="$route.path" router background-color="#001529"
               text-color="#c8c9cc" active-text-color="#409eff">
        <el-menu-item index="/dashboard"><el-icon><DataBoard /></el-icon>数据大屏</el-menu-item>
        <el-menu-item index="/price/query"><el-icon><Search /></el-icon>价格查询</el-menu-item>
        <el-menu-item index="/price/trend"><el-icon><TrendCharts /></el-icon>趋势分析</el-menu-item>
        <el-menu-item index="/price/compare"><el-icon><Histogram /></el-icon>地区对比</el-menu-item>
        <el-menu-item index="/feed"><el-icon><Wheat /></el-icon>饲料价格</el-menu-item>
        <el-menu-item index="/predict"><el-icon><MagicStick /></el-icon>价格预测</el-menu-item>
        <el-menu-item index="/analysis"><el-icon><Connection /></el-icon>关联分析</el-menu-item>
        <el-menu-item index="/alert"><el-icon><Bell /></el-icon>预警管理</el-menu-item>
        <el-menu-item index="/admin"><el-icon><Setting /></el-icon>后台管理</el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <span class="title">{{ $route.meta.title }}</span>
        <div class="right">
          <span class="username">{{ username }}</span>
          <el-button link type="danger" @click="handleLogout">退出登录</el-button>
        </div>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { logout } from '../api/auth'

const router = useRouter()
const username = computed(() => localStorage.getItem('username') || '未登录')

async function handleLogout() {
  try {
    await logout()
  } finally {
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    router.push('/login')
  }
}
</script>

<style scoped>
.layout { height: 100vh; }
.aside { background: #001529; }
.logo {
  height: 60px; line-height: 60px; text-align: center;
  color: #fff; font-weight: bold; font-size: 16px;
  border-bottom: 1px solid #16324f;
}
.aside :deep(.el-menu) { border-right: none; }
.header {
  background: #fff; display: flex; align-items: center;
  justify-content: space-between; box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
}
.title { font-size: 18px; font-weight: 600; }
.right { display: flex; align-items: center; gap: 12px; }
.username { color: #606266; }
.main { padding: 16px; overflow-y: auto; }
</style>
