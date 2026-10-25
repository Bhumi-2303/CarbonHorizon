import React from 'react'
import { Link } from 'react-router-dom'
import { Leaf, Code, Mail } from 'lucide-react'
import { CookieSettingsButton } from './CookieConsent'

interface PublicLayoutProps {
  children: React.ReactNode
}

export function PublicLayout({ children }: PublicLayoutProps) {
  return (
    <div className="min-h-screen bg-bg-primary font-sans text-primary selection:bg-earth-green/30 flex flex-col">
      {/* Public Header */}
      <header className="sticky top-0 z-40 bg-bg-primary/80 backdrop-blur-xl border-b border-white/10 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-20">
            <Link to="/" className="flex items-center gap-3 group focus:outline-none focus:ring-2 focus:ring-earth-green rounded-xl p-1">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-earth-green to-forest-green flex items-center justify-center text-space-black shadow-lg shadow-earth-green/20 group-hover:scale-105 transition-transform" aria-hidden="true">
                <Leaf className="w-6 h-6" />
              </div>
              <span className="font-poppins font-bold text-xl tracking-tight text-primary">
                Carbon Horizon
              </span>
            </Link>
            <nav className="flex items-center gap-4" aria-label="Public Navigation">
              <Link
                to="/login"
                className="text-sm font-semibold text-slate-300 hover:text-primary transition-colors focus:outline-none focus:ring-2 focus:ring-earth-green rounded-lg px-2 py-1"
              >
                Log In
              </Link>
              <Link
                to="/register"
                className="py-2 px-4 rounded-xl font-bold text-sm bg-earth-green text-white dark:text-slate-950 hover:bg-emerald-400 transition-colors shadow-md shadow-earth-green/20 focus:outline-none focus:ring-2 focus:ring-earth-green"
              >
                Sign Up Free
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 py-12 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto w-full">
        {children}
      </main>

      {/* Public Footer */}
      <footer className="border-t border-white/10 bg-bg-primary/95 pt-16 pb-12 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-12">
            <div className="md:col-span-2">
              <Link to="/" className="flex items-center gap-2 mb-4 group inline-flex">
                <Leaf className="w-6 h-6 text-earth-green group-hover:rotate-12 transition-transform" aria-hidden="true" />
                <span className="font-poppins font-bold text-xl text-primary">Carbon Horizon</span>
              </Link>
              <p className="text-slate-400 max-w-lg leading-relaxed text-sm">
                Empowering individuals and organizations to measure, understand, and reduce their environmental impact through AI-driven insights.
              </p>
            </div>
            <div>
              <p className="font-semibold text-primary mb-4 text-sm uppercase tracking-wider">Platform</p>
              <ul className="space-y-2.5 text-sm">
                <li>
                  <Link to="/" className="text-slate-400 hover:text-earth-green transition-colors">
                    Home
                  </Link>
                </li>
                <li>
                  <Link to="/login" className="text-slate-400 hover:text-earth-green transition-colors">
                    Log In
                  </Link>
                </li>
                <li>
                  <Link to="/register" className="text-slate-400 hover:text-earth-green transition-colors">
                    Sign Up
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <p className="font-semibold text-primary mb-4 text-sm uppercase tracking-wider">Legal & Privacy</p>
              <ul className="space-y-2.5 text-sm">
                <li>
                  <Link to="/privacy" className="text-slate-400 hover:text-earth-green transition-colors">
                    Privacy Policy
                  </Link>
                </li>
                <li>
                  <Link to="/terms" className="text-slate-400 hover:text-earth-green transition-colors">
                    Terms of Service
                  </Link>
                </li>
                <li>
                  <CookieSettingsButton />
                </li>
                <li className="pt-2 flex gap-4">
                  <a
                    href="https://github.com/CarbonHorizon"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-slate-400 hover:text-primary transition-colors"
                    aria-label="Carbon Horizon GitHub repository"
                  >
                    <Code className="w-5 h-5" aria-hidden="true" />
                  </a>
                  <a
                    href="mailto:contact@carbonhorizon.app"
                    className="text-slate-400 hover:text-primary transition-colors"
                    aria-label="Contact Carbon Horizon via email"
                  >
                    <Mail className="w-5 h-5" aria-hidden="true" />
                  </a>
                </li>
              </ul>
            </div>
          </div>
          <div className="border-t border-white/10 pt-8 flex flex-col md:flex-row items-center justify-between text-sm text-slate-500 gap-4">
            <p>© {new Date().getFullYear()} Carbon Horizon. All rights reserved.</p>
            <p>Built for a sustainable future.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default PublicLayout
