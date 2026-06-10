/**
 * AuthContext.tsx — in-memory JWT store + auth helpers
 *
 * Tokens are kept ONLY in React state (never localStorage/sessionStorage).
 * The axios client is updated via an interceptor whenever the access token
 * changes so every subsequent API call is automatically authenticated.
 *
 * Context value
 * -------------
 * user         — decoded profile, null when unauthenticated
 * isLoading    — true while the context initialises (future: silent refresh)
 * isAuthenticated — shorthand boolean
 * login()      — store tokens, set user, attach Bearer header
 * logout()     — clear everything
 * setUser()    — update profile after a PUT /profile call
 */
import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react'
import apiClient from '@/api/client'
import { authApi, type TokenResponse, type UserProfile } from '@/api/auth'

// ─── Types ───────────────────────────────────────────────────────────────────

interface AuthState {
  user: UserProfile | null
  accessToken: string | null
  refreshToken: string | null
}

interface AuthContextValue {
  user: UserProfile | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (tokens: TokenResponse, profile: UserProfile) => void
  logout: () => void
  setUser: (profile: UserProfile) => void
}

// ─── Context ────────────────────────────────────────────────────────────────

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

// ─── Provider ───────────────────────────────────────────────────────────────

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [auth, setAuth] = useState<AuthState>({
    user: null,
    accessToken: null,
    refreshToken: null,
  })
  const [isLoading] = useState(false)

  // Keep a ref so the axios interceptor can always read the latest token
  // without re-registering the interceptor on every render.
  const accessTokenRef = useRef<string | null>(null)

  // ── Attach Bearer header on every request ──────────────────────────────
  useEffect(() => {
    const interceptorId = apiClient.interceptors.request.use((config) => {
      const token = accessTokenRef.current
      if (token) {
        config.headers = config.headers ?? {}
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    })
    return () => apiClient.interceptors.request.eject(interceptorId)
  }, [])

  // ── login ───────────────────────────────────────────────────────────────
  const login = useCallback((tokens: TokenResponse, profile: UserProfile) => {
    accessTokenRef.current = tokens.access_token
    setAuth({
      user: profile,
      accessToken: tokens.access_token,
      refreshToken: tokens.refresh_token,
    })
  }, [])

  // ── logout ──────────────────────────────────────────────────────────────
  const logout = useCallback(async () => {
    // Best-effort server logout (invalidate server-side if blocklist is added)
    try {
      await authApi.logout()
    } catch {
      // ignore — we clear local state regardless
    }
    accessTokenRef.current = null
    setAuth({ user: null, accessToken: null, refreshToken: null })
  }, [])

  // ── setUser (after profile update) ─────────────────────────────────────
  const setUser = useCallback((profile: UserProfile) => {
    setAuth((prev) => ({ ...prev, user: profile }))
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user: auth.user,
      isLoading,
      isAuthenticated: auth.user !== null,
      login,
      logout,
      setUser,
    }),
    [auth.user, isLoading, login, logout, setUser],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// ─── Hook ────────────────────────────────────────────────────────────────────

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
