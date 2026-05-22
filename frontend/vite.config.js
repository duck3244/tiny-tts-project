import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 개발 시 /api 요청을 FastAPI(8000)로 프록시 → same-origin, CORS 불필요
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
