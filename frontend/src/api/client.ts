/**
 * Axios client — pre-configured for the Carbon Horizon API.
 * Token injection and refresh interceptors will be wired here when auth is implemented.
 */
import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15_000,
})

// Request interceptor — attach Bearer token from localStorage (to be replaced with store)
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor — handle 401 / token expiry (TODO: implement refresh logic)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // TODO: handle 401 → trigger refresh token flow
    return Promise.reject(error)
  }
)

export default apiClient
