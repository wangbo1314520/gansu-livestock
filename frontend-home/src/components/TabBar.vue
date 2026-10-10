<template>
  <div class="page">
    <!-- 页面主体 -->
    <div class="content">
      <router-view />
    </div>
    <!-- 底部导航（需求文档 9.3）：首页 / 价格 / 计算 / 我的 -->
    <van-tabbar route fixed placeholder>
      <van-tabbar-item replace to="/" icon="home-o">首页</van-tabbar-item>
      <van-tabbar-item replace to="/price" icon="chart-trending-o">价格</van-tabbar-item>
      <van-tabbar-item replace to="/calculator" icon="calculator-o">计算</van-tabbar-item>
      <van-tabbar-item replace to="/mine" icon="user-o">我的</van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<script setup>
// 家用版底部导航容器
</script>

<style scoped>
.content { min-height: 100vh; padding-bottom: env(safe-area-inset-bottom); }
</style>
