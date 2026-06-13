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
      
      {/* Sidebar Navigation (Desktop) */}
      <aside className="hidden md:flex flex-col w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 h-screen sticky top-0 flex-shrink-0">
        
        <div className="p-6 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center text-white shadow-sm shadow-emerald-500/20">
            <svg viewBox="0 0 24 24" className="w-5 h-5 fill-current">
              <path d="M17 8C8 10 5.9 16.17 3.82 21.34L5.71 22l1-2.3A4.49 4.49 0 0 0 8 20C19 20 22 3 22 3c-1 2-8 2-8 2 0 0-4 0-4 8" />
            </svg>
          </div>
          <span className="font-bold text-lg tracking-tight text-slate-900 dark:text-white">
            Carbon Horizon
          </span>
        </div>

        <nav className="flex-1 px-4 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-400'
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white'
                }`
              }
            >
              <i className={`ti ${item.icon} text-lg`}></i>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-slate-200 dark:border-slate-800">
          <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-4 flex flex-col gap-3">
            <div>
              <p className="text-sm font-semibold text-slate-900 dark:text-white truncate">
                {user?.full_name}
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Score: <span className="font-bold text-emerald-600 dark:text-emerald-400">{score}</span>
              </p>
            </div>
            <button
              onClick={handleLogout}
              className="text-xs text-left text-slate-500 hover:text-red-500 dark:text-slate-400 dark:hover:text-red-400 flex items-center gap-2 transition-colors w-max"
            >
              <i className="ti ti-logout"></i> Logout
            </button>
          </div>
        </div>

      </aside>

      {/* Main Content Area */}
      <main className="flex-1 min-w-0 pb-20 md:pb-0 relative">
        <Outlet />
      </main>

      {/* Bottom Navigation (Mobile) */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 flex items-center justify-around z-50 px-2 pb-safe">
        {NAV_ITEMS.slice(0, 5).map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex flex-col items-center justify-center p-3 min-w-[64px] ${
                isActive
                  ? 'text-emerald-600 dark:text-emerald-400'
                  : 'text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white'
              }`
            }
          >
            <i className={`ti ${item.icon} text-xl mb-1`}></i>
            <span className="text-[10px] font-medium leading-none">{item.label}</span>
          </NavLink>
        ))}
      </nav>

    </div>
  )
}
