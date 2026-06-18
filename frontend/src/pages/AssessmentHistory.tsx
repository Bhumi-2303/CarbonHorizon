/**
 * AssessmentHistory.tsx — Carbon Horizon
 *
 * Fetches GET /api/v1/assessment/history and renders a chronological list
 * of past footprint assessments. Each card shows:
 *   • Date & period
 *   • Total emission (kg CO₂e)
 *   • Carbon score with colour-coded badge
 *
 * Clicking any card navigates to /assessment/history/:id for the full breakdown.
 * A "Recalculate" button navigates back to the /assessment wizard.
 */
import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { assessmentApi, type AssessmentResult } from '@/api/assessment'
import { Car, Zap, Salad, Trash2 } from 'lucide-react'

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatDate(iso: string): string {
  return new Intl.DateTimeFormat('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  }).format(new Date(iso))
}

function formatEmission(val: number): string {
  return val.toLocaleString('en-IN', { maximumFractionDigits: 1 })
}

/** Returns Tailwind classes + label for the carbon score band */
function scoreBadge(score: number): { bg: string; text: string; ring: string; label: string } {
  if (score >= 75) return { bg: 'bg-earth-green/15', text: 'text-earth-green', ring: 'ring-earth-green/30', label: 'Excellent' }
  if (score >= 50) return { bg: 'bg-amber-500/15',   text: 'text-amber-400',   ring: 'ring-amber-500/30',   label: 'Moderate' }
  if (score >= 25) return { bg: 'bg-orange-500/15',  text: 'text-orange-400',  ring: 'ring-orange-500/30',  label: 'High'     }
  return             { bg: 'bg-rose-500/15',    text: 'text-rose-400',    ring: 'ring-rose-500/30',    label: 'Critical' }
}

function scoreGauge(score: number): string {
  if (score >= 75) return 'bg-earth-green'
  if (score >= 50) return 'bg-amber-500'
  if (score >= 25) return 'bg-orange-500'
  return 'bg-rose-500'
}

function periodLabel(p: string): string {
  const map: Record<string, string> = { monthly: 'Monthly', daily: 'Daily', annual: 'Annual' }
  return map[p] ?? p
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function Spinner() {
  return (
    <div className="flex items-center justify-center py-20">
      <div className="w-10 h-10 border-4 border-slate-700 border-t-emerald-500 rounded-full animate-spin" />
    </div>
  )
}

function ErrorBanner({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center gap-4 py-16 text-center">
      <div className="w-14 h-14 rounded-2xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-center">
        <svg className="w-7 h-7 text-rose-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
            d="M12 9v3m0 3h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
        </svg>
      </div>
      <div>
        <p className="text-slate-300 font-medium">Failed to load history</p>
        <p className="text-sm text-muted mt-1">{message}</p>
      </div>
      <button
        onClick={onRetry}
        className="px-5 py-2 rounded-xl text-sm font-medium text-earth-green border border-earth-green/40 hover:bg-earth-green/10 transition-colors"
      >
        Try again
      </button>
    </div>
  )
}

function EmptyState({ onRecalculate }: { onRecalculate: () => void }) {
  return (
    <div className="flex flex-col items-center gap-5 py-20 text-center">
      {/* Illustration */}
      <div className="relative">
        <div className="w-20 h-20 rounded-3xl bg-earth-green/10 border border-earth-green/20 flex items-center justify-center">
          <svg className="w-10 h-10 text-earth-green/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.2}
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
        </div>
        <div className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-earth-green/20 border border-earth-green/40 flex items-center justify-center">
          <span className="text-xs text-earth-green">0</span>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold text-slate-200">No assessments yet</h3>
        <p className="text-sm text-muted mt-1 max-w-xs mx-auto">
          Run your first carbon footprint assessment to start tracking your environmental impact.
        </p>
      </div>

      <button
        id="empty-state-recalculate"
        onClick={onRecalculate}
        className="flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-semibold text-white
          bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-400 hover:to-emerald-500
          shadow-lg shadow-emerald-500/25 transition-all duration-200"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        </svg>
        Start first assessment
      </button>
    </div>
  )
}

function AssessmentCard({
  item,
  rank,
  onClick,
}: {
  item: AssessmentResult
  rank: number
  onClick: () => void
}) {
  const badge  = scoreBadge(item.carbon_score)
  const gaugeColor = scoreGauge(item.carbon_score)

  return (
    <button
      id={`assessment-card-${item.assessment_id}`}
      type="button"
      onClick={onClick}
      className="w-full text-left group bg-deep-ocean/40 hover:bg-deep-ocean/70 border border-slate-700/50
        hover:border-slate-600 rounded-2xl p-5 transition-all duration-200 hover:shadow-lg
        hover:shadow-black/20 hover:-translate-y-0.5 focus-visible:outline-none
        focus-visible:ring-2 focus-visible:ring-earth-green/60"
    >
      <div className="flex items-start gap-4">
        {/* Rank pill */}
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-700/60 flex items-center justify-center">
          <span className="text-xs font-semibold text-muted">#{rank}</span>
        </div>

        <div className="flex-1 min-w-0">
          {/* Top row */}
          <div className="flex items-start justify-between gap-3 flex-wrap">
            <div>
              <p className="text-sm font-medium text-slate-200 group-hover:text-white transition-colors">
                {formatDate(item.created_at)}
              </p>
              <span className="inline-block mt-1 text-xs text-muted bg-slate-700/50 px-2 py-0.5 rounded-full">
                {periodLabel(item.assessment_period)}
              </span>
            </div>

            {/* Score badge */}
            <div className={`flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-xl ring-1 ${badge.bg} ${badge.ring}`}>
              <span className={`text-xl font-bold tabular-nums ${badge.text}`}>
                {item.carbon_score}
              </span>
              <div>
                <p className={`text-xs font-semibold ${badge.text}`}>/100</p>
                <p className={`text-xs ${badge.text} opacity-75`}>{badge.label}</p>
              </div>
            </div>
          </div>

          {/* Emission row */}
          <div className="mt-3 flex items-center justify-between gap-4">
            <div>
              <p className="text-xs text-muted mb-0.5">Total emission</p>
              <p className="text-lg font-bold text-slate-100 tabular-nums">
                {formatEmission(item.total_emission)}
                <span className="text-xs font-normal text-muted ml-1">kg CO₂e</span>
              </p>
            </div>

            {/* Mini emission bars */}
            <div className="hidden sm:flex flex-col gap-1 min-w-[140px]">
              {[
                { label: <Car className="w-4 h-4 inline-block text-[#2ECC71]" />, val: item.transport, total: item.total_emission },
                { label: <Zap className="w-4 h-4 inline-block text-[#2ECC71]" />, val: item.energy,    total: item.total_emission },
                { label: <Salad className="w-4 h-4 inline-block text-[#2ECC71]" />, val: item.food,      total: item.total_emission },
                { label: <Trash2 className="w-4 h-4 inline-block text-[#2ECC71]" />, val: item.waste,     total: item.total_emission },
              ].map(({ label, val, total }, idx) => (
                <div key={idx} className="flex items-center gap-2">
                  <span className="text-xs w-5 text-center">{label}</span>
                  <div className="flex-1 h-1.5 bg-slate-700/80 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-earth-green/70 rounded-full transition-all duration-500"
                      style={{ width: total > 0 ? `${Math.min((val / total) * 100, 100)}%` : '0%' }}
                    />
                  </div>
                  <span className="text-xs text-muted w-10 text-right tabular-nums">
                    {val.toFixed(0)}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Score gauge bar */}
          <div className="mt-3">
            <div className="h-1 bg-slate-700/60 rounded-full overflow-hidden">
              <div
                className={`h-full ${gaugeColor} rounded-full transition-all duration-700`}
                style={{ width: `${item.carbon_score}%` }}
              />
            </div>
          </div>
        </div>

        {/* Chevron */}
        <div className="flex-shrink-0 self-center text-muted group-hover:text-muted group-hover:translate-x-0.5 transition-all duration-200">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </div>
      </div>
    </button>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

type Status = 'idle' | 'loading' | 'success' | 'error'

export default function AssessmentHistory() {
  const navigate = useNavigate()
  const [status,  setStatus]  = useState<Status>('idle')
  const [items,   setItems]   = useState<AssessmentResult[]>([])
  const [errMsg,  setErrMsg]  = useState('')

  const fetchHistory = useCallback(async () => {
    setStatus('loading')
    setErrMsg('')
    try {
      const data = await assessmentApi.history()
      setItems(data)
      setStatus('success')
    } catch (err) {
      setErrMsg(err instanceof Error ? err.message : 'Something went wrong')
      setStatus('error')
    }
  }, [])

  useEffect(() => { fetchHistory() }, [fetchHistory])

  const goToDetail     = (id: string) => navigate(`/assessment/history/${id}`)
  const goToWizard     = () => navigate('/assessment')

  // ── Derived stats ────────────────────────────────────────────────────────
  const avgScore = items.length
    ? Math.round(items.reduce((s, i) => s + i.carbon_score, 0) / items.length)
    : null
  const avgEmission = items.length
    ? items.reduce((s, i) => s + i.total_emission, 0) / items.length
    : null
  const bestScore = items.length ? Math.max(...items.map((i) => i.carbon_score)) : null

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950 p-4 sm:p-8">
      {/* Background orbs */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 rounded-full bg-earth-green/6 blur-3xl" />
        <div className="absolute bottom-0 left-0 w-72 h-72 rounded-full bg-earth-green/20 blur-3xl" />
      </div>

      <div className="relative max-w-2xl mx-auto">

        {/* ── Header ── */}
        <div className="flex items-center justify-between gap-4 mb-8">
          <div>
            {/* Back link */}
            <button
              onClick={() => navigate('/dashboard')}
              className="flex items-center gap-1.5 text-xs text-muted hover:text-slate-300 mb-3 transition-colors"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Dashboard
            </button>

            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500/20 to-emerald-600/10
                border border-earth-green/30 flex items-center justify-center">
                <svg className="w-5 h-5 text-earth-green" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-100">Assessment History</h1>
                <p className="text-sm text-muted">
                  {status === 'success'
                    ? items.length
                      ? `${items.length} assessment${items.length !== 1 ? 's' : ''} recorded`
                      : 'No assessments yet'
                    : 'Your carbon footprint over time'}
                </p>
              </div>
            </div>
          </div>

          {/* Recalculate button */}
          <button
            id="recalculate-btn"
            onClick={goToWizard}
            className="flex-shrink-0 flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold
              text-white bg-gradient-to-r from-emerald-500 to-emerald-600
              hover:from-emerald-400 hover:to-emerald-500
              shadow-lg shadow-emerald-500/20 hover:shadow-emerald-500/35
              transition-all duration-200"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <span className="hidden sm:inline">Recalculate</span>
            <span className="sm:hidden">New</span>
          </button>
        </div>

        {/* ── Summary stats (shown when we have data) ── */}
        {status === 'success' && items.length > 0 && (
          <div className="grid grid-cols-3 gap-3 mb-6 animate-fade-in">
            {[
              {
                label: 'Avg Score',
                value: avgScore !== null ? String(avgScore) : '—',
                sub: 'out of 100',
                color: avgScore !== null ? scoreBadge(avgScore).text : 'text-muted',
              },
              {
                label: 'Best Score',
                value: bestScore !== null ? String(bestScore) : '—',
                sub: 'personal best',
                color: bestScore !== null ? scoreBadge(bestScore).text : 'text-muted',
              },
              {
                label: 'Avg Emission',
                value: avgEmission !== null ? avgEmission.toFixed(0) : '—',
                sub: 'kg CO₂e / period',
                color: 'text-slate-200',
              },
            ].map(({ label, value, sub, color }) => (
              <div
                key={label}
                className="bg-deep-ocean/50 border border-slate-700/50 rounded-2xl p-4 text-center"
              >
                <p className={`text-2xl font-bold tabular-nums ${color}`}>{value}</p>
                <p className="text-xs font-medium text-slate-300 mt-0.5">{label}</p>
                <p className="text-xs text-muted mt-0.5">{sub}</p>
              </div>
            ))}
          </div>
        )}

        {/* ── Content area ── */}
        {status === 'loading' && <Spinner />}

        {status === 'error' && (
          <ErrorBanner message={errMsg} onRetry={fetchHistory} />
        )}

        {status === 'success' && items.length === 0 && (
          <EmptyState onRecalculate={goToWizard} />
        )}

        {status === 'success' && items.length > 0 && (
          <div className="space-y-3 animate-fade-in">
            {/* Sorted newest-first (server already orders desc, but ensure it) */}
            {[...items]
              .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
              .map((item, idx) => (
                <AssessmentCard
                  key={item.assessment_id}
                  item={item}
                  rank={idx + 1}
                  onClick={() => goToDetail(item.assessment_id)}
                />
              ))}
          </div>
        )}
      </div>
    </div>
  )
}
