/**
 * Axios client — pre-configured for the Carbon Horizon API.
 *
 * Bearer token is injected by AuthContext's request interceptor.
 * The interceptor here is a fallback placeholder only.
 */
import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
  timeout: 15_000,
})

// Response interceptor — surface clean error messages from the APIResponse envelope
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Extract the backend error message if available
    const data = error.response?.data
    if (data && !data.success && data.error?.message) {
      return Promise.reject(new Error(data.error.message))
    }
    if (data?.detail) {
      return Promise.reject(new Error(data.detail))
    }
    return Promise.reject(error)
  },
)

export default apiClient
