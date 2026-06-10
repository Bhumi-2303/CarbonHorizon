/**
 * ProtectedRoute.tsx
 *
 * Guards all authenticated pages. Reads isAuthenticated + isLoading from
 * AuthContext and behaves as follows:
 *
 *  isLoading       → full-page spinner (silent token refresh in progress)
 *  isAuthenticated → render <Outlet /> (the nested page)
 *  otherwise       → <Navigate to="/login"> preserving the requested URL
 *                    so Login can redirect back after authentication.
 *
 * Usage in App.tsx:
 *   <Route element={<ProtectedRoute />}>
 *     <Route path="/dashboard" element={<Dashboard />} />
 *   </Route>
 */
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'

// ─── Loading screen ───────────────────────────────────────────────────────────

function AuthLoadingScreen() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950 flex flex-col items-center justify-center gap-4">
      {/* Animated logo mark */}
      <div className="relative">
        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center shadow-xl shadow-emerald-500/30 animate-pulse">
          <svg viewBox="0 0 24 24" className="w-7 h-7 text-white fill-current">
            <path d="M17 8C8 10 5.9 16.17 3.82 21.34L5.71 22l1-2.3A4.49 4.49 0 0 0 8 20C19 20 22 3 22 3c-1 2-8 2-8 2 0 0-4 0-4 8" />
          </svg>
        </div>
        {/* Spinning ring */}
        <div className="absolute inset-0 -m-1.5">
          <svg className="w-[68px] h-[68px] animate-spin" viewBox="0 0 68 68" fill="none">
            <circle
              cx="34" cy="34" r="31"
              stroke="url(#grad)" strokeWidth="3"
              strokeLinecap="round" strokeDasharray="48 145"
            />
            <defs>
              <linearGradient id="grad" x1="0" y1="0" x2="68" y2="68" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stopColor="hsl(152,72%,52%)" />
                <stop offset="100%" stopColor="hsl(152,72%,28%)" stopOpacity="0" />
              </linearGradient>
            </defs>
          </svg>
        </div>
      </div>

      <div className="text-center space-y-1">
        <p className="text-sm font-medium text-slate-300">Refreshing session…</p>
        <p className="text-xs text-slate-500">Please wait</p>
      </div>
    </div>
  )
}

// ─── Guard ────────────────────────────────────────────────────────────────────

export default function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  // Show spinner while a silent token refresh is in flight
  if (isLoading) {
    return <AuthLoadingScreen />
  }

  // Not authenticated — send to /login, preserving the requested URL
  // so Login can redirect back: navigate(location.state?.from ?? '/dashboard')
  if (!isAuthenticated) {
    return (
      <Navigate
        to="/login"
        state={{ from: location.pathname }}
        replace
      />
    )
  }

  // Authenticated — render the nested route
  return <Outlet />
}
