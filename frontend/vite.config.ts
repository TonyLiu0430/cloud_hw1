import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': {
        target: 'http://backend:5000', // Flask backend in docker compose
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
