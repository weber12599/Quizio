import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    allowedHosts: ['.trycloudflare.com'],
    proxy: {
      // Forward WebSocket requests
      '/ws': {
        target: 'http://backend:8000',
        changeOrigin: true,
        ws: true
      },
      // Forward standard API requests
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true
      }
    }
  }
});
