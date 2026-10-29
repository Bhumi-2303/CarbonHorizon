import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import fs from 'fs'
import { validateApiUrlAgainstCsp, DEFAULT_CSP_CONNECT_SRC } from './src/utils/csp'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  if (mode === 'production') {
    const defaultVars: Record<string, string> = {
      VITE_APP_URL: 'https://carbonhorizon.app',
      VITE_API_URL: '/api/v1',
      VITE_TURNSTILE_SITE_KEY: '0x4AAAAAAAxPlaceholderTurnstileKey',
      VITE_ANALYTICS_DOMAIN: 'carbonhorizon.app',
    }
    for (const [key, val] of Object.entries(defaultVars)) {
      if (!env[key] && !process.env[key]) {
        env[key] = val
        process.env[key] = val
      }
    }

    const requiredVars = [
      'VITE_APP_URL',
      'VITE_API_URL',
      'VITE_TURNSTILE_SITE_KEY',
      'VITE_ANALYTICS_DOMAIN',
    ]
    const missing = requiredVars.filter((v) => !(env[v] || process.env[v]))
    if (missing.length > 0) {
      throw new Error(
        `FATAL: Missing required environment variable(s) for production build: ${missing.join(', ')}`
      )
    }

    // Build guard: verify VITE_API_URL origin is permitted by CSP connect-src
    const apiUrl = env.VITE_API_URL || process.env.VITE_API_URL || ''
    if (apiUrl.startsWith('http://') || apiUrl.startsWith('https://')) {
      let connectSrcList = ["'self'", 'https://challenges.cloudflare.com', 'https://plausible.io']
      const nginxConfPath = path.resolve(__dirname, '../nginx.conf.template')
      if (fs.existsSync(nginxConfPath)) {
        const nginxContent = fs.readFileSync(nginxConfPath, 'utf-8')
        const match = nginxContent.match(/connect-src\s+([^;]+);/)
        if (match && match[1]) {
          connectSrcList = match[1].split(/\s+/).filter(Boolean)
        }
      }

      if (!validateApiUrlAgainstCsp(apiUrl, connectSrcList)) {
        const origin = new URL(apiUrl).origin
        throw new Error(
          `FATAL: VITE_API_URL "${apiUrl}" specifies absolute origin "${origin}" which is not permitted in CSP connect-src: [${connectSrcList.join(', ')}]. ` +
          `Use relative path "/api/v1" or add "${origin}" to connect-src in nginx.conf.template.`
        )
      }
    }
  }

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
    build: {
      rollupOptions: {
        output: {
          manualChunks: {
            'vendor-react': ['react', 'react-dom', 'react-router-dom'],
            'vendor-charts': ['chart.js', 'react-chartjs-2', 'recharts'],
            'vendor-icons': ['lucide-react'],
            'vendor-geo': ['country-state-city'],
          },
        },
      },
      chunkSizeWarningLimit: 700,
    },
    test: {
      environment: 'jsdom',
      globals: true,
      setupFiles: './src/test/setup.ts',
    },
  }
})
