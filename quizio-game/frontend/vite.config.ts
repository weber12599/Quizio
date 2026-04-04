import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
    plugins: [vue()],
    server: {
        host: '0.0.0.0',
        port: 5173,
        strictPort: true,
        allowedHosts: ['.trycloudflare.com'],
        proxy: {
            '/api': {
                target: process.env.VITE_API_PROXY_BASE_URL,
                changeOrigin: true
            },
            '/socket.io': {
                target: process.env.VITE_SOCKET_PROXY_BASE_URL,
                ws: true,
                changeOrigin: true
            }
        }
    }
})
