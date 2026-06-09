/**
 * Auth API service — no logic yet, stubs only.
 */
import apiClient from './client'

export const authApi = {
  login: (_email: string, _password: string) => {
    // TODO: POST /auth/login
    throw new Error('Not implemented')
  },

  refresh: (_refreshToken: string) => {
    // TODO: POST /auth/refresh
    throw new Error('Not implemented')
  },

  logout: () => {
    // TODO: POST /auth/logout
    throw new Error('Not implemented')
  },
}

export default authApi
