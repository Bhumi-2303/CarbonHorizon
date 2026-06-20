import { Outlet, useNavigate, NavLink } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { LogOut, Leaf } from 'lucide-react'
import ThemeToggle from '../ThemeToggle'

export default function StudentLayout() {
  const { logout, user } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-space-black flex flex-col font-sans">
      <header className="fixed top-4 left-4 right-4 z-50 flex items-center justify-between glass-card px-4 py-2 border-sky-500/20">
        <div className="flex items-center gap-3 pr-6 border-r border-slate-700/50">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-sky-400 to-indigo-500 flex items-center justify-center shadow-sm">
            <Leaf className="w-5 h-5 text-slate-900" />
          </div>
          <span className="font-poppins font-bold text-lg text-white hidden sm:block">
            Student Space
          </span>
        </div>
        
        <nav className="flex-1 px-4 flex items-center gap-2">
          <NavLink 
            to="/dashboard" 
            className={({ isActive }) => `px-4 py-2 rounded-xl font-bold transition-all ${isActive ? 'bg-sky-400/20 text-sky-400' : 'text-slate-400 hover:text-white'}`}
          >
            Dashboard
          </NavLink>
          <NavLink 
            to="/coach" 
            className={({ isActive }) => `px-4 py-2 rounded-xl font-bold transition-all ${isActive ? 'bg-indigo-400/20 text-indigo-400' : 'text-slate-400 hover:text-white'}`}
          >
            AI Coach
          </NavLink>
        </nav>

        <div className="flex items-center gap-4 pl-6 border-l border-slate-700/50">
          <p className="text-sm font-bold text-sky-400 hidden sm:block">
            Hi, {user?.full_name?.split(' ')[0]}!
          </p>
          <ThemeToggle />
          <button
            onClick={handleLogout}
            className="p-2 rounded-xl text-slate-400 hover:bg-rose-500/10 hover:text-rose-400 transition-colors"
            title="Logout"
          >
            <LogOut className="w-5 h-5" />
          </button>
        </div>
      </header>

      <div className="flex-1 flex flex-col pt-24 pb-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
        <main className="flex-1 w-full animate-fade-shift-up">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
