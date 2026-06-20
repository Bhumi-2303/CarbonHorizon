import { useEffect, useState, useRef } from 'react'
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { assessmentApi, type AssessmentResult } from '@/api/assessment'
import {
  Leaf, Home, ClipboardList, Bot, LineChart, FileText, User,
  MoreHorizontal, LogOut, Menu, X, Target, Heart, History, Settings,
  FlaskConical, TrendingUp, Building2, Compass
} from 'lucide-react'
import ThemeToggle from './ThemeToggle'

const PRIMARY_NAV = [
  { path: '/dashboard', label: 'Home', icon: Home },
  { path: '/assessment', label: 'Assessment', icon: ClipboardList },
  { path: '/coach', label: 'AI Coach', icon: Bot },
  { path: '/emissions', label: 'Analytics', icon: LineChart },
  { path: '/reports', label: 'Reports', icon: FileText },
  { path: '/journey', label: 'Journey', icon: Compass },
  { path: '/profile', label: 'Profile', icon: User },
]

const MORE_NAV = [
  { path: '/simulator', label: 'Simulator', icon: FlaskConical },
  { path: '/forecast', label: 'Forecast', icon: TrendingUp },
  { path: '/goals', label: 'Goals', icon: Target },
  { path: '/habits', label: 'Habits', icon: Heart },
  { path: '/assessment/history', label: 'History', icon: History },
  { path: '/settings', label: 'Settings', icon: Settings },
  { path: '/organization', label: 'Organization', icon: Building2 },
]

export default function AppLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  
  const [latestAssessment, setLatestAssessment] = useState<AssessmentResult | null>(null)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [moreMenuOpen, setMoreMenuOpen] = useState(false)
  
  const moreMenuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Fetch latest assessment to display carbon score
    assessmentApi.history()
      .then(data => setLatestAssessment(data[0] || null))
      .catch(() => {})
      
    // Close mobile menu on route change
    setMobileMenuOpen(false)
    setMoreMenuOpen(false)
  }, [location.pathname])

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (moreMenuRef.current && !moreMenuRef.current.contains(event.target as Node)) {
        setMoreMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const score = latestAssessment ? latestAssessment.carbon_score.toFixed(0) : 'N/A'

  return (
    <div className="min-h-screen bg-bg-primary flex flex-col font-sans">
      <a href="#main-content" className="skip-to-content">
        Skip to main content
      </a>
      
      {/* ── Floating Navigation Bar (Desktop) ── */}
      <header className="fixed top-4 left-4 right-4 z-50 flex items-center justify-between glass-card px-4 py-2 hidden md:flex transition-all duration-300">
        
        {/* Brand / Logo */}
        <div className="flex items-center gap-3 pr-6 border-r border-slate-700/50">
          <div className="w-8 h-8 rounded-lg bg-accent flex items-center justify-center text-bg-primary shadow-sm" aria-hidden="true">
            <Leaf className="w-5 h-5" />
          </div>
          <span className="font-poppins font-bold text-lg tracking-tight text-white hidden lg:block">
            Carbon Horizon
          </span>
        </div>

        {/* Primary Links */}
        <nav className="flex-1 px-4 flex items-center gap-1" aria-label="Main Navigation">
          {PRIMARY_NAV.map(item => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-accent/10 text-accent nav-glow'
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                }`
              }
            >
              <item.icon className="w-4 h-4" aria-hidden="true" />
              <span className="hidden xl:block">{item.label}</span>
            </NavLink>
          ))}

          {/* More Dropdown */}
          <div className="relative ml-2" ref={moreMenuRef}>
            <button
              type="button"
              onClick={() => setMoreMenuOpen(!moreMenuOpen)}
              className={`flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
                moreMenuOpen ? 'bg-white/10 text-white' : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
              aria-expanded={moreMenuOpen}
              aria-haspopup="true"
            >
              <MoreHorizontal className="w-4 h-4" />
              <span className="hidden xl:block">More</span>
            </button>

            {moreMenuOpen && (
              <div className="absolute top-full left-0 mt-2 w-48 glass-card border border-slate-700/50 p-2 flex flex-col gap-1 shadow-xl animate-fade-shift-up">
                {MORE_NAV.map(item => (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                        isActive ? 'bg-accent/10 text-accent' : 'text-slate-300 hover:bg-white/5 hover:text-white'
                      }`
                    }
                  >
                    <item.icon className="w-4 h-4" />
                    {item.label}
                  </NavLink>
                ))}
              </div>
            )}
          </div>
        </nav>

        {/* User Status & Logout */}
        <div className="flex items-center gap-4 pl-6 border-l border-slate-700/50">
          <div className="hidden lg:block text-right">
            <p className="text-xs font-semibold text-white truncate max-w-[120px]">
              {user?.full_name}
            </p>
            <p className="text-[10px] text-slate-400">
              Score: <span className="font-bold text-accent">{score}</span>
            </p>
          </div>
          <ThemeToggle />
          <button
            onClick={handleLogout}
            className="p-2 rounded-xl text-slate-400 hover:bg-red-500/10 hover:text-red-400 transition-colors"
            aria-label="Logout"
            title="Logout"
          >
            <LogOut className="w-5 h-5" />
          </button>
        </div>
      </header>

      {/* ── Mobile Navigation Bar ── */}
      <header className="md:hidden fixed top-0 left-0 right-0 z-50 glass-card rounded-none border-t-0 border-x-0 border-b border-slate-700/50 p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-accent flex items-center justify-center text-bg-primary" aria-hidden="true">
            <Leaf className="w-5 h-5" />
          </div>
          <span className="font-poppins font-bold text-white">Carbon Horizon</span>
        </div>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 text-slate-300 hover:text-white"
            aria-label="Toggle mobile menu"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </header>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden fixed inset-0 z-40 pt-20 pb-safe px-4 bg-bg-primary/95 backdrop-blur-xl overflow-y-auto animate-fade-in">
          <nav className="flex flex-col gap-2 pb-8">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2 mt-4 px-2">Primary</p>
            {PRIMARY_NAV.map(item => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 rounded-xl font-medium transition-colors ${
                    isActive ? 'bg-accent/10 text-accent nav-glow' : 'text-slate-300 hover:bg-white/5'
                  }`
                }
              >
                <item.icon className="w-5 h-5" />
                {item.label}
              </NavLink>
            ))}
            
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2 mt-6 px-2">More Tools</p>
            {MORE_NAV.map(item => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 rounded-xl font-medium transition-colors ${
                    isActive ? 'bg-accent/10 text-accent' : 'text-slate-300 hover:bg-white/5'
                  }`
                }
              >
                <item.icon className="w-5 h-5" />
                {item.label}
              </NavLink>
            ))}

            <div className="mt-8 pt-6 border-t border-slate-700/50 px-2">
              <p className="text-sm font-semibold text-white mb-1">{user?.full_name}</p>
              <p className="text-xs text-slate-400 mb-6">Latest Score: <span className="text-accent font-bold">{score}</span></p>
              <button
                onClick={handleLogout}
                className="flex items-center gap-3 text-red-400 hover:text-red-300 w-full px-2 py-3"
              >
                <LogOut className="w-5 h-5" />
                Logout
              </button>
            </div>
          </nav>
        </div>
      )}

      {/* ── Main Content Area ── */}
      <div className="flex-1 flex flex-col pt-20 md:pt-24 pb-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full relative">
        <main
          id="main-content"
          tabIndex={-1}
          key={location.pathname}
          className="flex-1 outline-none animate-fade-shift-up w-full"
        >
          <Outlet />
        </main>
      </div>

    </div>
  )
}
