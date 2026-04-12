import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Proxy /analyse, /health, /frames, /annotated to FastAPI on port 8000
      '/analyse':  { target: 'http://localhost:8000', changeOrigin: true },
      '/health':   { target: 'http://localhost:8000', changeOrigin: true },
      '/frames':   { target: 'http://localhost:8000', changeOrigin: true },
      '/annotated':{ target: 'http://localhost:8000', changeOrigin: true },
    },
  },
})
