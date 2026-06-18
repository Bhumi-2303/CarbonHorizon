import { useEffect, useState } from 'react'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { assessmentApi, type AssessmentResult } from '@/api/assessment'

const NAV_ITEMS = [
  { path: '/dashboard', label: 'Dashboard', icon: 'ti-home' },
  { path: '/assessment', label: 'Assessment', icon: 'ti-clipboard' },
  { path: '/simulator', label: 'Simulator', icon: 'ti-flask' },
  { path: '/forecast', label: 'Forecast', icon: 'ti-chart-line' },
  { path: '/goals', label: 'Goals', icon: 'ti-target' },
  { path: '/habits', label: 'Habits', icon: 'ti-leaf' },
  { path: '/coach', label: 'AI Coach', icon: 'ti-robot' },
  { path: '/assessment/history', label: 'History', icon: 'ti-history' },
]

export default function AppLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  
  const [latestAssessment, setLatestAssessment] = useState<AssessmentResult | null>(null)

  useEffect(() => {
    // Fetch latest assessment to display carbon score
    assessmentApi.history()
      .then(data => setLatestAssessment(data[0] || null))
      .catch(() => {
        // Suppress 404s if user hasn't completed an assessment yet
      })
  }, [])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const score = latestAssessment ? latestAssessment.carbon_score.toFixed(0) : 'N/A'

  return (
    <div className="min-h-screen bg-[var(--color-bg-primary)] flex flex-col md:flex-row">
      <a href="#main-content" className="skip-to-content">
        Skip to main content
      </a>
      
      {/* Sidebar Navigation (Desktop) */}
      <aside className="hidden md:flex flex-col w-64 bg-deep-ocean dark:bg-deep-ocean border-r border-slate-200 border-deep-ocean h-screen sticky top-0 flex-shrink-0" aria-label="Sidebar Navigation">
        
        <div className="p-6 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center text-white shadow-sm shadow-emerald-500/20" aria-hidden="true">
            <svg viewBox="0 0 24 24" className="w-5 h-5 fill-current">
              <path d="M17 8C8 10 5.9 16.17 3.82 21.34L5.71 22l1-2.3A4.49 4.49 0 0 0 8 20C19 20 22 3 22 3c-1 2-8 2-8 2 0 0-4 0-4 8" />
            </svg>
          </div>
          <span className="font-bold text-lg tracking-tight text-white text-white">
            Carbon Horizon
          </span>
        </div>

        <nav className="flex-1 px-4 space-y-1 overflow-y-auto" aria-label="Main Navigation">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-emerald-50 text-emerald-700 dark:bg-earth-green/20 dark:text-earth-green'
                    : 'text-muted hover:bg-deep-ocean hover:text-white dark:text-muted dark:hover:bg-deep-ocean dark:hover:text-white'
                }`
              }
            >
              <i className={`ti ${item.icon} text-lg`} aria-hidden="true"></i>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-slate-200 border-deep-ocean">
          <div className="bg-deep-ocean dark:bg-deep-ocean/50 rounded-xl p-4 flex flex-col gap-3">
            <div>
              <p className="text-sm font-semibold text-white text-white truncate">
                {user?.full_name}
              </p>
              <p className="text-xs text-muted dark:text-muted">
                Score: <span className="font-bold text-earth-green dark:text-earth-green">{score}</span>
              </p>
            </div>
            <button
              onClick={handleLogout}
              className="text-xs text-left text-muted hover:text-red-500 dark:text-muted dark:hover:text-red-400 flex items-center gap-2 transition-colors w-max"
              aria-label="Logout from account"
            >
              <i className="ti ti-logout" aria-hidden="true"></i> Logout
            </button>
          </div>
        </div>

      </aside>

      {/* Main Content Area */}
      <main id="main-content" tabIndex={-1} className="flex-1 min-w-0 pb-20 md:pb-0 relative outline-none">
        <Outlet />
      </main>

      {/* Bottom Navigation (Mobile) */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-deep-ocean dark:bg-deep-ocean border-t border-slate-200 border-deep-ocean flex items-center justify-around z-50 px-2 pb-safe" aria-label="Mobile Navigation">
        {NAV_ITEMS.slice(0, 5).map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex flex-col items-center justify-center p-3 min-w-[64px] ${
                isActive
                  ? 'text-earth-green dark:text-earth-green'
                  : 'text-muted hover:text-white dark:text-muted dark:hover:text-white'
              }`
            }
          >
            <i className={`ti ${item.icon} text-xl mb-1`} aria-hidden="true"></i>
            <span className="text-[10px] font-medium leading-none">{item.label}</span>
          </NavLink>
        ))}
      </nav>

    </div>
  )
}
