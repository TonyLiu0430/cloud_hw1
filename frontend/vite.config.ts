import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import Pages from 'vite-plugin-pages'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    Pages(),
    tailwindcss(),
  ],
  server: {
    allowedHosts: ['secondhand.cloudlinux.win'],
    host: '0.0.0.0',
    port: 3000,
  }
})
