/**
 * AuthLayout.tsx — centred card layout shared by Register and Login pages.
 * Renders a glassmorphism card on a gradient dark background.
 */
import React from 'react'

export function AuthLayout({
  children,
  title,
  subtitle,
}: {
  children: React.ReactNode
  title: string
  subtitle: string
}) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950 flex items-center justify-center p-4">
      {/* Background decorative orbs */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-96 h-96 rounded-full bg-emerald-500/10 blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 rounded-full bg-emerald-600/8 blur-3xl" />
      </div>

      <div className="relative w-full max-w-md">
        {/* Logo mark */}
        <div className="flex items-center gap-2.5 mb-8 justify-center">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center shadow-lg shadow-emerald-500/30">
            <svg viewBox="0 0 24 24" className="w-5 h-5 text-white fill-current">
              <path d="M17 8C8 10 5.9 16.17 3.82 21.34L5.71 22l1-2.3A4.49 4.49 0 0 0 8 20C19 20 22 3 22 3c-1 2-8 2-8 2 0 0-4 0-4 8" />
            </svg>
          </div>
          <span className="text-xl font-semibold tracking-tight text-slate-100">
            Carbon<span className="text-emerald-400">Horizon</span>
          </span>
        </div>

        {/* Card */}
        <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-700/50 rounded-2xl shadow-2xl shadow-black/40 p-8">
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-slate-100">{title}</h1>
            <p className="mt-1 text-sm text-slate-400">{subtitle}</p>
          </div>
          {children}
        </div>
      </div>
    </div>
  )
}
