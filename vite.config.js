import { defineConfig } from 'vite'
import { resolve } from 'node:path'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    proxy: {
      '/litellm': {
        target: 'http://localhost:4000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/litellm/, ''),
      },
      '/api': {
        target: 'http://localhost:5174',
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      input: {
        // Marketing homepage at /
        main: resolve(__dirname, 'index.html'),
        // BookWizard / Workspace app at /app.html
        app: resolve(__dirname, 'app.html'),
        // Brand kit visual smoke test at /brand-sample.html
        brandSample: resolve(__dirname, 'brand-sample.html'),
      },
    },
  },
})
