import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 学校版开发服务器 5173，后端 5000
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
    },
  },
})
