import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'node:url'

function normalizeAllowedHost(value) {
  const candidate = value.trim()
  if (!candidate) return null

  try {
    const url = candidate.includes('://') ? candidate : `https://${candidate}`
    return new URL(url).hostname
  } catch {
    return candidate
  }
}

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, fileURLToPath(new URL('.', import.meta.url)), '')
  const allowedHosts = env.VITE_ALLOWED_HOST
    ? env.VITE_ALLOWED_HOST.split(',').map(normalizeAllowedHost).filter(Boolean)
    : []

  return {
    plugins: [react()],
    server: {
      host: '0.0.0.0',
      port: 5173,
      strictPort: true,
      allowedHosts,
      proxy: {
        '/api': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
      },
    },
    build: {
      rollupOptions: {
        input: {
          main: fileURLToPath(new URL('./index.html', import.meta.url)),
          fasConfig: fileURLToPath(new URL('./fas-config.html', import.meta.url)),
          dynamicFas: fileURLToPath(new URL('./dynamic-fas.html', import.meta.url)),
        },
      },
    },
  }
})
