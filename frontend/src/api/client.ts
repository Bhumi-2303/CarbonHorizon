/**
 * Axios client — pre-configured for the Carbon Horizon API.
 *
 * Bearer token is injected by AuthContext's request interceptor.
 * The interceptor here is a fallback placeholder only.
 */
import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  headers: { 'Content-Type': 'application/json' },
  timeout: 15_000,
})

// Response interceptor — surface clean error messages from the APIResponse envelope
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const data = error.response?.data
    
    // Server responded with an error payload
    if (data) {
      if (data.message) {
        return Promise.reject(new Error(data.message))
      }
      if (data.error?.message) {
        return Promise.reject(new Error(data.error.message))
      }
      if (data.detail) {
        return Promise.reject(new Error(data.detail))
      }
    }
    
    // Server did not respond (Network Error, CORS, etc.)
    if (error.request && !error.response) {
      return Promise.reject(new Error("Unable to connect. Please try again later."))
    }
    
    // Generic fallback for anything else
    return Promise.reject(new Error("An unexpected error occurred. Please try again."))
  },
)

export default apiClient
