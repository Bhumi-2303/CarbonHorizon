/**
 * SimulatorHistory.tsx — Carbon Horizon
 *
 * Lists saved simulation scenarios from GET /api/v1/simulator/history.
 * Each card shows: date, scenario name, current vs projected emission,
 * carbon_saved, reduction_percentage badge.
 * "New Simulation" → /simulator
 */
import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { simulatorApi, type SimulationSaved } from '@/api/simulator'

function formatDate(iso: string) {
  return new Intl.DateTimeFormat('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit', hour12: true,
  }).format(new Date(iso))
}

function reductionColor(pct: number | null) {
  if (pct === null) return { text: 'text-slate-400', bg: 'bg-slate-700/40', ring: 'ring-slate-600/30' }
  if (pct >= 30) return { text: 'text-emerald-400', bg: 'bg-emerald-500/15', ring: 'ring-emerald-500/30' }
  if (pct >= 10) return { text: 'text-amber-400',   bg: 'bg-amber-500/15',   ring: 'ring-amber-500/30'   }
  if (pct > 0)   return { text: 'text-orange-400',  bg: 'bg-orange-500/15',  ring: 'ring-orange-500/30'  }
  return               { text: 'text-rose-400',    bg: 'bg-rose-500/15',    ring: 'ring-rose-500/30'    }
}

function Spinner() {
  return (
    <div className="flex items-center justify-center py-20">
      <div className="w-10 h-10 border-4 border-slate-700 border-t-emerald-500 rounded-full animate-spin" />
    </div>
  )
}

function EmptyState({ onNew }: { onNew: () => void }) {
  return (
    <div className="flex flex-col items-center gap-5 py-20 text-center">
      <div className="w-20 h-20 rounded-3xl bg-emerald-500/10 border border-emerald-500/20
        flex items-center justify-center">
        <svg className="w-10 h-10 text-emerald-500/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.2}
            d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      </div>
      <div>
        <h3 className="text-lg font-semibold text-slate-200">No saved simulations</h3>
        <p className="text-sm text-slate-500 mt-1 max-w-xs mx-auto">
          Run a what-if scenario and save it to see your scenarios here.
        </p>
      </div>
      <button
        onClick={onNew}
        className="flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-semibold text-white
          bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-400 hover:to-emerald-500
          shadow-lg shadow-emerald-500/25 transition-all duration-200"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        </svg>
        New Simulation
      </button>
    </div>
  )
}

function SimCard({ item }: { item: SimulationSaved }) {
  const col = reductionColor(item.reduction_percentage)

  return (
    <div className="bg-slate-800/40 border border-slate-700/50 rounded-2xl p-5
      hover:border-slate-600 hover:bg-slate-800/60 transition-all duration-200">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <p className="text-sm font-semibold text-slate-100">{item.scenario_name}</p>
          <p className="text-xs text-slate-500 mt-0.5">{formatDate(item.created_at)}</p>
        </div>
        {/* Reduction badge */}
        {item.reduction_percentage !== null && (
          <div className={`flex-shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-xl
            ring-1 ${col.bg} ${col.ring}`}>
            <span className={`text-sm font-bold tabular-nums ${col.text}`}>
              {item.reduction_percentage >= 0 ? '−' : '+'}
              {Math.abs(item.reduction_percentage).toFixed(1)}%
            </span>
          </div>
        )}
      </div>

      {/* Emission comparison */}
      {item.current_emission !== null && item.projected_emission !== null && (
        <div className="mt-4 grid grid-cols-3 gap-3">
          <div className="text-center">
            <p className="text-xs text-slate-500">Current</p>
            <p className="text-base font-bold text-slate-300 tabular-nums mt-0.5">
              {item.current_emission.toFixed(1)}
            </p>
            <p className="text-xs text-slate-600">kg CO₂e</p>
          </div>
          <div className="flex items-center justify-center">
            <svg className="w-5 h-5 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 8l4 4m0 0l-4 4m4-4H3" />
            </svg>
          </div>
          <div className="text-center">
            <p className="text-xs text-slate-500">Projected</p>
            <p className={`text-base font-bold tabular-nums mt-0.5 ${col.text}`}>
              {item.projected_emission.toFixed(1)}
            </p>
            <p className="text-xs text-slate-600">kg CO₂e</p>
          </div>
        </div>
      )}

      {/* Carbon saved */}
      {item.estimated_carbon_saved !== null && (
        <div className="mt-3 pt-3 border-t border-slate-700/40 flex items-center justify-between">
          <span className="text-xs text-slate-500">Monthly saving</span>
          <span className={`text-xs font-semibold tabular-nums ${col.text}`}>
            {item.estimated_carbon_saved >= 0 ? '−' : '+'}
            {Math.abs(item.estimated_carbon_saved).toFixed(1)} kg CO₂e
          </span>
        </div>
      )}

      {/* Changes applied pill list */}
      {item.simulation_data?.changes_applied &&
        Object.keys(item.simulation_data.changes_applied).length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {Object.entries(item.simulation_data.changes_applied).map(([k, v]) => (
            <span key={k}
              className="text-xs bg-slate-900/60 border border-slate-700/50 text-slate-400
                px-2 py-0.5 rounded-full">
              {k.replace(/_/g, ' ')}: {v}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

export default function SimulatorHistory() {
  const navigate = useNavigate()
  const [status, setStatus] = useState<'loading' | 'ok' | 'error'>('loading')
  const [items,  setItems]  = useState<SimulationSaved[]>([])
  const [errMsg, setErrMsg] = useState('')

  const fetchHistory = useCallback(async () => {
    setStatus('loading')
    try {
      const data = await simulatorApi.history()
      setItems(data)
      setStatus('ok')
    } catch (err) {
      setErrMsg(err instanceof Error ? err.message : 'Failed to load history')
      setStatus('error')
    }
  }, [])

  useEffect(() => { fetchHistory() }, [fetchHistory])

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950 p-4 sm:p-8">
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 rounded-full bg-emerald-500/6 blur-3xl" />
        <div className="absolute bottom-0 left-0 w-72 h-72 rounded-full bg-emerald-700/5 blur-3xl" />
      </div>

      <div className="relative max-w-2xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between gap-4 mb-8">
          <div>
            <button
              onClick={() => navigate('/simulator')}
              className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-300 mb-3 transition-colors"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Simulator
            </button>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500/20 to-emerald-600/10
                border border-emerald-500/30 flex items-center justify-center">
                <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-100">Simulation History</h1>
                <p className="text-sm text-slate-400">
                  {status === 'ok'
                    ? items.length
                      ? `${items.length} scenario${items.length !== 1 ? 's' : ''} saved`
                      : 'No saved scenarios'
                    : 'Your saved what-if scenarios'}
                </p>
              </div>
            </div>
          </div>

          <button
            id="new-simulation-btn"
            onClick={() => navigate('/simulator')}
            className="flex-shrink-0 flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold
              text-white bg-gradient-to-r from-emerald-500 to-emerald-600
              hover:from-emerald-400 hover:to-emerald-500
              shadow-lg shadow-emerald-500/20 transition-all duration-200"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            <span className="hidden sm:inline">New Simulation</span>
            <span className="sm:hidden">New</span>
          </button>
        </div>

        {status === 'loading' && <Spinner />}

        {status === 'error' && (
          <div className="flex flex-col items-center gap-4 py-16 text-center">
            <p className="text-slate-300">{errMsg}</p>
            <button onClick={fetchHistory}
              className="text-sm text-emerald-400 border border-emerald-500/40 px-4 py-2
                rounded-xl hover:bg-emerald-500/10 transition-colors">
              Retry
            </button>
          </div>
        )}

        {status === 'ok' && items.length === 0 && (
          <EmptyState onNew={() => navigate('/simulator')} />
        )}

        {status === 'ok' && items.length > 0 && (
          <div className="space-y-3 animate-fade-in">
            {items.map(item => (
              <SimCard key={item.id} item={item} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
