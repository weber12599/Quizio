import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    // Allow external access in Docker
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: ['.trycloudflare.com'],
    proxy: {
      // Forward all /ws requests to the FastAPI backend container
      '/ws': {
        target: 'ws://backend:8000',
        changeOrigin: true,
        ws: true,
      }
    }
  }
})
