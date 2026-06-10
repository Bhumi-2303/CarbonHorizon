/**
 * AuthContext.tsx — in-memory JWT store with auto-refresh
 *
 * Design principles
 * -----------------
 * 1. Tokens ONLY in React state — never localStorage/sessionStorage.
 *    Mitigates XSS token theft; tabs don't share state (acceptable trade-off).
 *
 * 2. Auto-refresh via setTimeout — a timer is scheduled whenever new tokens
 *    arrive. It fires at (expires_in - REFRESH_BUFFER_SECONDS) so the access
 *    token is silently rotated before the server rejects it.
 *
 * 3. Single axios interceptor — stored in a ref so it is registered once and
 *    always reads the latest token without re-mounting.
 *
 * 4. isLoading — true during the initial silent-refresh attempt and any
 *    subsequent refresh call, so ProtectedRoute can show a spinner instead
 *    of flashing /login on a cold page load.
 *
 * Context API
 * -----------
 * user            UserProfile | null
 * accessToken     string | null          (exposed for debugging / tests)
 * isLoading       boolean
 * isAuthenticated boolean
 * login()         store tokens + profile, schedule auto-refresh
 * logout()        cancel timer, clear state, POST /auth/logout
 * refreshToken()  call POST /auth/refresh, store new pair, reschedule timer
 * setUser()       patch profile after PUT /profile
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

// ─── Constants ────────────────────────────────────────────────────────────────

/**
 * Fire the silent refresh this many seconds BEFORE the access token expires.
 * e.g. expires_in=1800 → timer fires at 1740 s (1 min before expiry).
 */
const REFRESH_BUFFER_SECONDS = 60

// ─── Types ────────────────────────────────────────────────────────────────────

interface AuthState {
  user: UserProfile | null
  accessToken: string | null
  refreshToken: string | null
  /** Unix timestamp (ms) when the access token expires */
  expiresAt: number | null
}

export interface AuthContextValue {
  user: UserProfile | null
  accessToken: string | null
  isLoading: boolean
  isAuthenticated: boolean
  /** Store tokens + profile after a successful login or registration. */
  login: (tokens: TokenResponse, profile: UserProfile) => void
  /**
   * Silently refresh the access token using the stored refresh token.
   * Resolves with the new TokenResponse on success.
   * Rejects (and calls logout) if the refresh token is invalid / expired.
   */
  refreshToken: () => Promise<TokenResponse>
  /** Clear all auth state and POST /auth/logout (best-effort). */
  logout: () => Promise<void>
  /** Update the user profile object after a PUT /profile call. */
  setUser: (profile: UserProfile) => void
}

// ─── Context ─────────────────────────────────────────────────────────────────

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

// ─── Helpers ─────────────────────────────────────────────────────────────────

/** Compute the expiry timestamp from the token's expires_in field. */
function expiresAtFromTTL(expiresInSeconds: number): number {
  return Date.now() + expiresInSeconds * 1000
}

/** Milliseconds until we should fire the refresh timer. */
function msUntilRefresh(expiresAt: number): number {
  const bufferMs = REFRESH_BUFFER_SECONDS * 1000
  return Math.max(expiresAt - Date.now() - bufferMs, 0)
}

// ─── Provider ─────────────────────────────────────────────────────────────────

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [auth, setAuth] = useState<AuthState>({
    user: null,
    accessToken: null,
    refreshToken: null,
    expiresAt: null,
  })
  const [isLoading, setIsLoading] = useState(false)

  // Refs — stable across renders, safe to read inside callbacks/interceptors
  const accessTokenRef  = useRef<string | null>(null)
  const refreshTokenRef = useRef<string | null>(null)
  const refreshTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // ── Clear the pending refresh timer ────────────────────────────────────
  const clearRefreshTimer = useCallback(() => {
    if (refreshTimerRef.current !== null) {
      clearTimeout(refreshTimerRef.current)
      refreshTimerRef.current = null
    }
  }, [])

  // ── Axios request interceptor (registered once) ─────────────────────────
  useEffect(() => {
    const id = apiClient.interceptors.request.use((config) => {
      const token = accessTokenRef.current
      if (token) {
        config.headers = config.headers ?? {}
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    })
    return () => {
      apiClient.interceptors.request.eject(id)
    }
  }, [])

  // ── Cleanup timer on unmount ────────────────────────────────────────────
  useEffect(() => () => clearRefreshTimer(), [clearRefreshTimer])

  // ── Schedule the silent refresh timer ──────────────────────────────────
  // Declared with useCallback so we can call it from both login and refreshToken.
  // Note: refreshToken is passed as a parameter to break the circular dep.
  const scheduleRefresh = useCallback(
    (expiresAt: number, doRefresh: () => Promise<TokenResponse>) => {
      clearRefreshTimer()
      const delay = msUntilRefresh(expiresAt)
      refreshTimerRef.current = setTimeout(() => {
        doRefresh().catch(() => {
          // If silent refresh fails the doRefresh impl calls logout internally
        })
      }, delay)
    },
    [clearRefreshTimer],
  )

  // ── Internal state updater used by login + refreshToken ────────────────
  const applyTokens = useCallback(
    (tokens: TokenResponse, profile: UserProfile | null) => {
      const expiresAt = expiresAtFromTTL(tokens.expires_in)
      accessTokenRef.current  = tokens.access_token
      refreshTokenRef.current = tokens.refresh_token
      setAuth((prev) => ({
        user: profile ?? prev.user,
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
        expiresAt,
      }))
      return expiresAt
    },
    [],
  )

  // ── refreshToken ────────────────────────────────────────────────────────
  /**
   * Silently refreshes the access token.
   * - Reads the stored refresh token from the ref (stable, no stale closure).
   * - On success: stores new tokens, reschedules the timer.
   * - On failure: calls logout() so the user is sent back to /login.
   */
  const refreshToken = useCallback(async (): Promise<TokenResponse> => {
    const storedRefresh = refreshTokenRef.current
    if (!storedRefresh) {
      throw new Error('No refresh token available')
    }

    setIsLoading(true)
    try {
      const tokens = await authApi.refresh(storedRefresh)
      const expiresAt = applyTokens(tokens, null)

      // Re-schedule — doRefresh here refers to the same refreshToken fn;
      // we pass it after defining it to avoid circular deps at declaration time.
      scheduleRefresh(expiresAt, refreshToken)

      return tokens
    } catch (err) {
      // Refresh token invalid/expired — log the user out
      // We call logout() directly here; it is defined below but hoisted via ref.
      logoutRef.current?.()
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [applyTokens, scheduleRefresh])

  // Store refreshToken in a ref so scheduleRefresh and the logout fallback
  // can reference it without stale closures.
  const refreshTokenFnRef = useRef(refreshToken)
  useEffect(() => { refreshTokenFnRef.current = refreshToken }, [refreshToken])

  // ── logout ──────────────────────────────────────────────────────────────
  const logout = useCallback(async (): Promise<void> => {
    clearRefreshTimer()
    accessTokenRef.current  = null
    refreshTokenRef.current = null

    setAuth({
      user: null,
      accessToken: null,
      refreshToken: null,
      expiresAt: null,
    })

    // Best-effort server-side invalidation
    try {
      await authApi.logout()
    } catch {
      // ignore — local state is already cleared
    }
  }, [clearRefreshTimer])

  // Ref so refreshToken's error path can call logout without a circular dep
  const logoutRef = useRef(logout)
  useEffect(() => { logoutRef.current = logout }, [logout])

  // ── login ───────────────────────────────────────────────────────────────
  const login = useCallback(
    (tokens: TokenResponse, profile: UserProfile) => {
      const expiresAt = applyTokens(tokens, profile)
      scheduleRefresh(expiresAt, () => refreshTokenFnRef.current())
    },
    [applyTokens, scheduleRefresh],
  )

  // ── setUser ─────────────────────────────────────────────────────────────
  const setUser = useCallback((profile: UserProfile) => {
    setAuth((prev) => ({ ...prev, user: profile }))
  }, [])

  // ── Context value ───────────────────────────────────────────────────────
  const value = useMemo<AuthContextValue>(
    () => ({
      user: auth.user,
      accessToken: auth.accessToken,
      isLoading,
      isAuthenticated: auth.user !== null,
      login,
      logout,
      refreshToken,
      setUser,
    }),
    [auth.user, auth.accessToken, isLoading, login, logout, refreshToken, setUser],
  )

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

/**
 * useAuth — access the AuthContext.
 * Must be called inside a component wrapped by <AuthProvider>.
 */
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
