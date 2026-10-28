import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  server: {
    port: 3000,
    open: true,
    // 本地 e2e 验收:浏览器(Docker)经 host.docker.internal 访问。仅 dev server。
    allowedHosts: ['localhost', 'host.docker.internal'],
    proxy: {
      // 默认代理常规后端 :8000(全站共用·勿为单页改默认)。
      // 验 control-plane(/control 闭环回放)时本地 dev server 在 :8077:
      //   cd phase3/backend && python scripts/run_control_plane_local.py
      //   然后 VITE_API_PROXY=http://127.0.0.1:8077 npm run dev
      '/api': {
        target: process.env.VITE_API_PROXY || 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          'vendor-ui': ['framer-motion', 'zustand'],
          'vendor-ethers': ['ethers'],
          'vendor-query': ['@tanstack/react-query'],
          'vendor-forms': ['react-hook-form', '@hookform/resolvers', 'zod'],
        }
      }
    }
  }
})
