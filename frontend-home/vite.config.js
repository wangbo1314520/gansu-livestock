import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 家用版开发服务器 5174，后端 5000
// Vant 在 main.js 全量注册（家用版页面多、体量小，全量引入足够）
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5174,
    host: '0.0.0.0',          // 手机同局域网可直接访问
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
    },
  },
})
