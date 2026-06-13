/**
 * AssessmentDetail.tsx — Carbon Horizon
 *
 * Fetches GET /api/v1/assessment/:id and renders the full breakdown for
 * a single carbon assessment. Accessible at /assessment/history/:id.
 *
 * Shows:
 *   • Carbon score dial with colour band
 *   • Total emission headline
 *   • Per-category bars (transport, energy, food, waste)
 *   • Metadata (period, date)
 *   • "Recalculate" and "← Back" navigation
 */
import { useEffect, useState, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { assessmentApi, type AssessmentResult } from '@/api/assessment'

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatDate(iso: string): string {
  return new Intl.DateTimeFormat('en-IN', {
    weekday: 'long',
    day: '2-digit',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  }).format(new Date(iso))
}

function periodLabel(p: string): string {
  const map: Record<string, string> = { monthly: 'Monthly', daily: 'Daily', annual: 'Annual' }
  return map[p] ?? p
}

function scoreBand(score: number) {
  if (score >= 75) return { color: '#10b981', label: 'Excellent', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', text: 'text-emerald-400' }
  if (score >= 50) return { color: '#f59e0b', label: 'Moderate', bg: 'bg-amber-500/10',   border: 'border-amber-500/30',   text: 'text-amber-400' }
  if (score >= 25) return { color: '#f97316', label: 'High',     bg: 'bg-orange-500/10',  border: 'border-orange-500/30',  text: 'text-orange-400' }
  return                  { color: '#ef4444', label: 'Critical', bg: 'bg-rose-500/10',    border: 'border-rose-500/30',    text: 'text-rose-400' }
}

// Polar-arc SVG gauge
function ScoreDial({ score }: { score: number }) {
  const band = scoreBand(score)
  const radius   = 52
  const strokeW  = 8
  const cx = 64, cy = 64
  const circumference = Math.PI * radius          // half-circle arc length
  const progress = (score / 100) * circumference  // filled portion

  return (
    <div className="flex flex-col items-center gap-2">
      <svg width={128} height={80} viewBox="0 0 128 80" className="overflow-visible">
        {/* Track */}
        <path
          d={`M ${cx - radius} ${cy} A ${radius} ${radius} 0 0 1 ${cx + radius} ${cy}`}
          fill="none" stroke="#1e293b" strokeWidth={strokeW} strokeLinecap="round"
        />
        {/* Progress */}
        <path
          d={`M ${cx - radius} ${cy} A ${radius} ${radius} 0 0 1 ${cx + radius} ${cy}`}
          fill="none"
          stroke={band.color}
          strokeWidth={strokeW}
          strokeLinecap="round"
          strokeDasharray={`${progress} ${circumference}`}
          style={{ filter: `drop-shadow(0 0 6px ${band.color}60)` }}
        />
        {/* Score text */}
        <text x={cx} y={cy - 4} textAnchor="middle" fill="white" fontSize="22" fontWeight="700" fontFamily="Inter, sans-serif">
          {score}
        </text>
        <text x={cx} y={cy + 14} textAnchor="middle" fill="#64748b" fontSize="10" fontFamily="Inter, sans-serif">
          / 100
        </text>
      </svg>
      <span className={`text-sm font-semibold ${band.text}`}>{band.label}</span>
    </div>
  )
}

// Horizontal bar for a category
function CategoryBar({
  emoji,
  label,
  value,
  total,
  colorClass,
}: {
  emoji: string
  label: string
  value: number
  total: number
  colorClass: string
}) {
  const pct = total > 0 ? Math.min((value / total) * 100, 100) : 0

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2">
          <span className="text-base leading-none">{emoji}</span>
          <span className="text-slate-300 font-medium">{label}</span>
        </div>
        <div className="text-right">
          <span className="text-slate-100 font-semibold tabular-nums">{value.toFixed(1)}</span>
          <span className="text-slate-500 text-xs ml-1">kg CO₂e</span>
          <span className="text-slate-600 text-xs ml-1.5">({pct.toFixed(0)}%)</span>
        </div>
      </div>
      <div className="h-2.5 bg-slate-700/50 rounded-full overflow-hidden">
        <div
          className={`h-full ${colorClass} rounded-full transition-all duration-700 ease-out`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

// ─── Spinner / Error ──────────────────────────────────────────────────────────

function Spinner() {
  return (
    <div className="flex items-center justify-center py-32">
      <div className="w-10 h-10 border-4 border-slate-700 border-t-emerald-500 rounded-full animate-spin" />
    </div>
  )
}

function ErrorState({ message, onBack }: { message: string; onBack: () => void }) {
  return (
    <div className="flex flex-col items-center gap-4 py-24 text-center">
      <div className="w-14 h-14 rounded-2xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-center">
        <svg className="w-7 h-7 text-rose-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
            d="M12 9v3m0 3h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
        </svg>
      </div>
      <div>
        <p className="text-slate-300 font-medium">Assessment not found</p>
        <p className="text-sm text-slate-500 mt-1">{message}</p>
      </div>
      <button
        onClick={onBack}
        className="px-5 py-2 rounded-xl text-sm font-medium text-emerald-400
          border border-emerald-500/40 hover:bg-emerald-500/10 transition-colors"
      >
        ← Back to history
      </button>
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

type Status = 'idle' | 'loading' | 'success' | 'error'

export default function AssessmentDetail() {
  const { id }        = useParams<{ id: string }>()
  const navigate      = useNavigate()
  const [status, setStatus]   = useState<Status>('idle')
  const [result, setResult]   = useState<AssessmentResult | null>(null)
  const [errMsg, setErrMsg]   = useState('')

  const fetchDetail = useCallback(async () => {
    if (!id) return
    setStatus('loading')
    try {
      const data = await assessmentApi.getById(id)
      setResult(data)
      setStatus('success')
    } catch (err) {
      setErrMsg(err instanceof Error ? err.message : 'Something went wrong')
      setStatus('error')
    }
  }, [id])

  useEffect(() => { fetchDetail() }, [fetchDetail])

  const band = result ? scoreBand(result.carbon_score) : null

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950 p-4 sm:p-8">
      {/* Background orbs */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 rounded-full bg-emerald-500/6 blur-3xl" />
        <div className="absolute bottom-0 left-0 w-72 h-72 rounded-full bg-emerald-700/5 blur-3xl" />
      </div>

      <div className="relative max-w-xl mx-auto">

        {/* ── Header ── */}
        <div className="flex items-center justify-between gap-3 mb-8">
          <button
            id="back-to-history"
            onClick={() => navigate('/assessment/history')}
            className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-slate-200
              transition-colors group"
          >
            <svg className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform"
              fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            History
          </button>

          <button
            id="recalculate-from-detail"
            onClick={() => navigate('/assessment')}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold text-white
              bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-400 hover:to-emerald-500
              shadow-lg shadow-emerald-500/20 transition-all duration-200"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Recalculate
          </button>
        </div>

        {/* ── States ── */}
        {status === 'loading' && <Spinner />}
        {status === 'error'   && (
          <ErrorState message={errMsg} onBack={() => navigate('/assessment/history')} />
        )}

        {status === 'success' && result && band && (
          <div className="space-y-4 animate-fade-in">

            {/* Hero card — score + total */}
            <div className={`${band.bg} border ${band.border} rounded-2xl p-6 text-center`}>
              <ScoreDial score={result.carbon_score} />

              <div className="mt-4 pt-4 border-t border-slate-700/50">
                <p className="text-xs text-slate-500 uppercase tracking-widest mb-1">Total Emission</p>
                <p className="text-4xl font-bold text-slate-100 tabular-nums">
                  {result.total_emission.toFixed(1)}
                  <span className="text-lg font-normal text-slate-400 ml-2">kg CO₂e</span>
                </p>
                <p className="text-xs text-slate-500 mt-2">
                  {periodLabel(result.assessment_period)} assessment
                </p>
              </div>
            </div>

            {/* Breakdown card */}
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6 space-y-5">
              <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide">
                Emission Breakdown
              </h2>

              <CategoryBar
                emoji="🚗"
                label="Transport"
                value={result.transport}
                total={result.total_emission}
                colorClass="bg-sky-500"
              />
              <CategoryBar
                emoji="⚡"
                label="Energy"
                value={result.energy}
                total={result.total_emission}
                colorClass="bg-amber-500"
              />
              <CategoryBar
                emoji="🥗"
                label="Food"
                value={result.food}
                total={result.total_emission}
                colorClass="bg-emerald-500"
              />
              <CategoryBar
                emoji="🗑️"
                label="Waste"
                value={result.waste}
                total={result.total_emission}
                colorClass="bg-rose-500"
              />
            </div>

            {/* Metadata card */}
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-5 space-y-3">
              <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide">Details</h2>

              {[
                { label: 'Recorded on',         value: formatDate(result.created_at) },
                { label: 'Assessment period',   value: periodLabel(result.assessment_period) },
                { label: 'Assessment ID',        value: result.assessment_id.slice(0, 8).toUpperCase() + '…' },
              ].map(({ label, value }) => (
                <div key={label} className="flex justify-between items-start gap-4 py-2 border-b border-slate-700/40 last:border-0">
                  <span className="text-sm text-slate-500 flex-shrink-0">{label}</span>
                  <span className="text-sm text-slate-200 text-right font-medium">{value}</span>
                </div>
              ))}
            </div>

            {/* Tips banner based on highest category */}
            {(() => {
              const cats = [
                { key: 'transport', val: result.transport, emoji: '🚗', tip: 'Try cycling or public transport for short trips to reduce transport emissions.' },
                { key: 'energy',    val: result.energy,    emoji: '⚡', tip: 'Switch off appliances at standby and consider LED lighting to cut energy use.' },
                { key: 'food',      val: result.food,      emoji: '🥗', tip: 'Reducing red meat consumption can significantly lower your food footprint.' },
                { key: 'waste',     val: result.waste,     emoji: '🗑️', tip: 'Increase recycling and switch to reusable bags and bottles.' },
              ]
              const top = cats.reduce((a, b) => (a.val > b.val ? a : b))
              if (top.val <= 0) return null
              return (
                <div className="flex items-start gap-3 p-4 bg-emerald-500/8 border border-emerald-500/20 rounded-2xl">
                  <span className="text-2xl flex-shrink-0">{top.emoji}</span>
                  <div>
                    <p className="text-sm font-semibold text-emerald-300 mb-1">💡 Tip — reduce your {top.key} footprint</p>
                    <p className="text-xs text-slate-400 leading-relaxed">{top.tip}</p>
                  </div>
                </div>
              )
            })()}

          </div>
        )}
      </div>
    </div>
  )
}
