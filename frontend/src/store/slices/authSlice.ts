/**
 * Auth Redux slice — no logic yet, structure only.
 */
import { createSlice } from '@reduxjs/toolkit'

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  loading: boolean
  error: string | null
}

const initialState: AuthState = {
  accessToken: null,
  refreshToken: null,
  isAuthenticated: false,
  loading: false,
  error: null,
}

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    // TODO: implement login, logout, tokenRefresh reducers
  },
})

export default authSlice.reducer
