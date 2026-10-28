/**
 * Axios client — pre-configured for the Carbon Horizon API.
 *
 * Bearer token is injected by AuthContext's request interceptor.
 * The interceptor here is a fallback placeholder only.
 */
import axios from 'axios'

export function resolveApiBaseUrl(rawUrl?: string): string {
  const url = (rawUrl || '/api/v1').trim().replace(/\/+$/, '')
  if (!url) return '/api/v1'
  if (url === '/api/v1') return '/api/v1'
  if (!url.endsWith('/api/v1')) {
    return `${url}/api/v1`
  }
  return url
}

export function extractErrorMessage(error: any): string {
  const status = error.response?.status
  const data = error.response?.data

  // If server responded with an error payload
  if (data && typeof data === 'object') {
    // 1. Explicit message from backend APIResponse envelope
    if (typeof data.message === 'string' && data.message.trim()) {
      return data.message
    }
    // 2. ErrorDetail object from backend: { error: { code: '...', message: '...' } }
    if (data.error && typeof data.error === 'object' && typeof data.error.message === 'string') {
      // Guard against Vercel/CDN 404 text being passed as an API error
      if (status === 404 && data.error.message.toLowerCase().includes('page could not be found')) {
        return 'API endpoint not found (404). Please verify service configuration.'
      }
      return data.error.message
    }
    if (typeof data.error === 'string' && data.error.trim()) {
      return data.error
    }
    // 3. FastAPI / Pydantic validation details
    if (data.detail) {
      if (typeof data.detail === 'string' && data.detail.trim()) {
        if (status === 404 && data.detail === 'Not Found') {
          return 'Requested resource not found (404).'
        }
        return data.detail
      }
      if (Array.isArray(data.detail)) {
        const msgs = data.detail
          .map((item: any) => {
            if (typeof item === 'string') return item
            const loc = Array.isArray(item.loc) ? item.loc.filter((p: any) => p !== 'body').join('.') : ''
            const msg = item.msg || item.message || JSON.stringify(item)
            return loc ? `${loc}: ${msg}` : msg
          })
          .filter(Boolean)
        if (msgs.length > 0) {
          return msgs.join(', ')
        }
      }
    }
  }

  // If server returned a 404 HTML string or unknown 404
  if (status === 404) {
    return 'API endpoint not found (404). Please verify service configuration.'
  }

  // If string payload (e.g. non-JSON error or platform 502/503)
  if (typeof data === 'string' && data.trim()) {
    // Avoid dumping HTML markup into user UI
    if (data.includes('<html') || data.includes('<!DOCTYPE')) {
      return `Server error (${status || 'unknown'}). Please try again later.`
    }
    return data.slice(0, 300)
  }

  // Server did not respond (Network Error, CORS, offline)
  if (error.request && !error.response) {
    return 'Unable to connect to the server. Please check your internet connection or verify service status.'
  }

  return 'An unexpected error occurred. Please try again.'
}

const apiClient = axios.create({
  baseURL: resolveApiBaseUrl(import.meta.env.VITE_API_URL),
  headers: { 'Content-Type': 'application/json' },
  timeout: 15_000,
})

// Response interceptor — surface clean error messages from the APIResponse envelope
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    return Promise.reject(new Error(extractErrorMessage(error)))
  },
)

export default apiClient
