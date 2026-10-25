import { Link } from 'react-router-dom'
import { Compass, Home, LayoutDashboard, ArrowLeft } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import Seo from '@/components/Seo'
import { SEO_PAGES } from '@/config/seo'

export default function NotFoundPage() {
  const { isAuthenticated } = useAuth()

  return (
    <div className="min-h-screen bg-bg-primary text-primary flex flex-col items-center justify-center p-4 sm:p-6 relative overflow-hidden font-sans">
      <Seo {...SEO_PAGES.notFound} />

      {/* Background ambient lighting */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-earth-green/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-ocean-blue/10 rounded-full blur-3xl pointer-events-none" />

      <main className="glass-panel p-8 sm:p-12 max-w-lg w-full rounded-3xl border border-white/10 shadow-2xl flex flex-col items-center text-center relative z-10 animate-fade-in">
        {/* Visual Icon */}
        <div className="w-20 h-20 rounded-2xl bg-earth-green/15 text-earth-green flex items-center justify-center mb-6 shadow-inner border border-earth-green/30">
          <Compass className="w-10 h-10 animate-pulse" aria-hidden="true" />
        </div>

        {/* 404 Badge */}
        <span className="text-xs font-bold uppercase tracking-widest text-earth-green bg-earth-green/10 px-3 py-1 rounded-full mb-3 border border-earth-green/20">
          Error 404
        </span>

        <h1 className="text-2xl sm:text-3xl font-bold font-poppins text-primary mb-3">
          Uncharted Territory
        </h1>

        <p className="text-slate-300 text-sm leading-relaxed mb-8 max-w-sm">
          The horizon you are looking for does not exist or has shifted. Let&apos;s get you back on track toward a sustainable future.
        </p>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center gap-3 w-full">
          {isAuthenticated ? (
            <>
              <Link
                to="/dashboard"
                className="w-full sm:w-1/2 py-3 px-5 rounded-xl font-bold text-sm bg-earth-green text-white dark:text-slate-950 hover:bg-emerald-400 transition-all flex items-center justify-center gap-2 shadow-lg shadow-earth-green/20 focus:outline-none focus:ring-2 focus:ring-earth-green"
              >
                <LayoutDashboard className="w-4 h-4" aria-hidden="true" />
                Dashboard
              </Link>
              <Link
                to="/"
                className="w-full sm:w-1/2 py-3 px-5 rounded-xl font-semibold text-sm border border-white/20 bg-white/5 text-primary hover:bg-white/10 transition-colors flex items-center justify-center gap-2 focus:outline-none focus:ring-2 focus:ring-earth-green"
              >
                <Home className="w-4 h-4" aria-hidden="true" />
                Home
              </Link>
            </>
          ) : (
            <>
              <Link
                to="/"
                className="w-full sm:w-1/2 py-3 px-5 rounded-xl font-bold text-sm bg-earth-green text-white dark:text-slate-950 hover:bg-emerald-400 transition-all flex items-center justify-center gap-2 shadow-lg shadow-earth-green/20 focus:outline-none focus:ring-2 focus:ring-earth-green"
              >
                <Home className="w-4 h-4" aria-hidden="true" />
                Return Home
              </Link>
              <Link
                to="/login"
                className="w-full sm:w-1/2 py-3 px-5 rounded-xl font-semibold text-sm border border-white/20 bg-white/5 text-primary hover:bg-white/10 transition-colors flex items-center justify-center gap-2 focus:outline-none focus:ring-2 focus:ring-earth-green"
              >
                <ArrowLeft className="w-4 h-4" aria-hidden="true" />
                Sign In
              </Link>
            </>
          )}
        </div>
      </main>

      <footer className="mt-8 text-xs text-slate-500 relative z-10">
        © {new Date().getFullYear()} Carbon Horizon
      </footer>
    </div>
  )
}
