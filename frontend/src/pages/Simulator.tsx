/**
 * Simulator.tsx — Carbon Horizon What-If Simulator
 *
 * Layout: two-column (stacked on mobile)
 *   LEFT  — Scenario Builder: toggle cards for each change type
 *   RIGHT — Live Results: bar chart (Recharts), stats, Save + History actions
 *
 * Flow:
 *   1. On mount: fetch latest assessment from GET /assessment/history[0]
 *      to use as the current-emission baseline.
 *   2. User toggles scenario cards and tunes knobs.
 *   3. "Run Simulation" → POST /simulator/run → populates right panel.
 *   4. "Save Scenario"  → POST /simulator/save.
 *   5. "View History"   → navigate('/simulator/history').
 */
import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, Legend,
} from 'recharts'

import { assessmentApi, type AssessmentResult } from '@/api/assessment'
import {
  simulatorApi,
  type SimulationResult,
  type ScenarioChanges,
  type TransportMode,
  type DietType,
} from '@/api/simulator'

// ─── Colour helpers ───────────────────────────────────────────────────────────

function reductionColor(pct: number) {
  if (pct >= 30) return { text: 'text-emerald-400', bg: 'bg-emerald-500/15', ring: 'ring-emerald-500/30' }
  if (pct >= 10) return { text: 'text-amber-400',   bg: 'bg-amber-500/15',   ring: 'ring-amber-500/30'   }
  if (pct > 0)   return { text: 'text-orange-400',  bg: 'bg-orange-500/15',  ring: 'ring-orange-500/30'  }
  return               { text: 'text-rose-400',    bg: 'bg-rose-500/15',    ring: 'ring-rose-500/30'    }
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function Spinner({ size = 'md' }: { size?: 'sm' | 'md' }) {
  const cls = size === 'sm' ? 'w-5 h-5 border-2' : 'w-10 h-10 border-4'
  return (
    <div className={`${cls} border-slate-700 border-t-emerald-500 rounded-full animate-spin`} />
  )
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-3">
      {children}
    </p>
  )
}

// Toggle card used in the scenario builder
function ToggleCard({
  id, emoji, title, subtitle, active, onClick, children,
}: {
  id: string
  emoji: string
  title: string
  subtitle: string
  active: boolean
  onClick: () => void
  children?: React.ReactNode
}) {
  return (
    <div
      className={`rounded-2xl border transition-all duration-200 overflow-hidden
        ${active
          ? 'border-emerald-500/50 bg-emerald-500/8 shadow-lg shadow-emerald-500/10'
          : 'border-slate-700/50 bg-slate-800/40 hover:border-slate-600'
        }`}
    >
      <button
        id={id}
        type="button"
        onClick={onClick}
        className="w-full flex items-center gap-3 p-4 text-left"
      >
        <span className="text-2xl flex-shrink-0">{emoji}</span>
        <div className="flex-1 min-w-0">
          <p className={`text-sm font-semibold ${active ? 'text-emerald-300' : 'text-slate-200'}`}>
            {title}
          </p>
          <p className="text-xs text-slate-500 mt-0.5 truncate">{subtitle}</p>
        </div>
        {/* Toggle pill */}
        <div className={`flex-shrink-0 w-9 h-5 rounded-full transition-colors duration-200 relative
          ${active ? 'bg-emerald-500' : 'bg-slate-700'}`}>
          <div className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-all duration-200
            ${active ? 'left-[18px]' : 'left-0.5'}`} />
        </div>
      </button>
      {/* Expanded knobs */}
      {active && children && (
        <div className="px-4 pb-4 pt-0 border-t border-emerald-500/20 animate-fade-in">
          {children}
        </div>
      )}
    </div>
  )
}

// Tiny slider + value label
function SliderRow({
  label, value, min, max, step = 1, unit,
  onChange,
}: {
  label: string
  value: number
  min: number
  max: number
  step?: number
  unit: string
  onChange: (v: number) => void
}) {
  return (
    <div className="mt-3">
      <div className="flex justify-between items-center mb-1">
        <span className="text-xs text-slate-400">{label}</span>
        <span className="text-xs font-semibold text-emerald-400 tabular-nums">
          {value}{unit}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={e => onChange(Number(e.target.value))}
        className="w-full h-1.5 bg-slate-700 rounded-full appearance-none cursor-pointer
          [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4
          [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:rounded-full
          [&::-webkit-slider-thumb]:bg-emerald-500 [&::-webkit-slider-thumb]:cursor-pointer"
      />
    </div>
  )
}

// Custom Recharts tooltip
function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-3 text-xs shadow-xl">
      <p className="font-semibold text-slate-300 mb-2">{label}</p>
      {payload.map((p: any) => (
        <p key={p.name} className="flex justify-between gap-4" style={{ color: p.color }}>
          <span>{p.name}</span>
          <span className="font-bold tabular-nums">{p.value.toFixed(1)} kg</span>
        </p>
      ))}
    </div>
  )
}

// Empty right-panel placeholder
function ResultsPlaceholder() {
  return (
    <div className="flex flex-col items-center justify-center h-64 gap-4 text-center">
      <div className="w-16 h-16 rounded-2xl bg-slate-800/60 border border-slate-700/50
        flex items-center justify-center">
        <svg className="w-8 h-8 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.2}
            d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      </div>
      <div>
        <p className="text-sm font-medium text-slate-400">No results yet</p>
        <p className="text-xs text-slate-600 mt-1">
          Toggle scenario changes on the left, then click Run Simulation.
        </p>
      </div>
    </div>
  )
}

// ─── Scenario state ───────────────────────────────────────────────────────────

interface ScenarioState {
  // Transport
  transportActive:   boolean
  newMode:           TransportMode
  newDistanceKm:     number

  // Energy
  energyActive:            boolean
  electricityReductionPct: number
  reducedAc:               boolean
  solarAdoption:           boolean

  // Food
  foodActive:   boolean
  newDietType:  DietType

  // Waste
  wasteActive:          boolean
  recyclingImprovement: number
  plasticReduction:     number
}

const DEFAULT_STATE: ScenarioState = {
  transportActive:         false,
  newMode:                 'bus',
  newDistanceKm:           0,
  energyActive:            false,
  electricityReductionPct: 20,
  reducedAc:               false,
  solarAdoption:           false,
  foodActive:              false,
  newDietType:             'vegetarian',
  wasteActive:             false,
  recyclingImprovement:    2,
  plasticReduction:        2,
}

function buildChanges(s: ScenarioState): ScenarioChanges {
  const changes: ScenarioChanges = {}
  if (s.transportActive) {
    changes.transport = { new_mode: s.newMode }
    if (s.newDistanceKm > 0) changes.transport.new_distance_km = s.newDistanceKm
  }
  if (s.energyActive) {
    changes.energy = {}
    if (s.electricityReductionPct > 0)
      changes.energy.electricity_reduction_pct = s.electricityReductionPct
    if (s.reducedAc)     changes.energy.reduced_ac    = true
    if (s.solarAdoption) changes.energy.solar_adoption = true
  }
  if (s.foodActive) {
    changes.food = { new_diet_type: s.newDietType }
  }
  if (s.wasteActive) {
    changes.waste = {}
    if (s.recyclingImprovement > 0)
      changes.waste.recycling_improvement = s.recyclingImprovement
    if (s.plasticReduction > 0)
      changes.waste.plastic_reduction = s.plasticReduction
  }
  return changes
}

const TRANSPORT_OPTIONS: { value: TransportMode; label: string; emoji: string }[] = [
  { value: 'bus',      label: 'Bus',      emoji: '🚌' },
  { value: 'train',    label: 'Train',    emoji: '🚆' },
  { value: 'bicycle',  label: 'Bicycle',  emoji: '🚴' },
  { value: 'car',      label: 'Car',      emoji: '🚗' },
  { value: 'motorcycle', label: 'Bike',   emoji: '🏍️' },
  { value: 'flight',   label: 'Flight',   emoji: '✈️' },
]

const DIET_OPTIONS: { value: DietType; label: string; emoji: string }[] = [
  { value: 'vegetarian',     label: 'Vegetarian',     emoji: '🥗' },
  { value: 'mixed',          label: 'Mixed',          emoji: '🍽️' },
  { value: 'non_vegetarian', label: 'Non-Vegetarian', emoji: '🥩' },
]

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function Simulator() {
  const navigate = useNavigate()

  // Baseline
  const [baseline,       setBaseline]       = useState<AssessmentResult | null>(null)
  const [baselineStatus, setBaselineStatus] = useState<'loading' | 'ok' | 'error'>('loading')

  // Scenario builder state
  const [sc, setSc] = useState<ScenarioState>(DEFAULT_STATE)

  // Run state
  const [running,    setRunning]    = useState(false)
  const [runError,   setRunError]   = useState('')
  const [result,     setResult]     = useState<SimulationResult | null>(null)
  const [scenarioName, setScenarioName] = useState('My Scenario')

  // Save state
  const [saving,   setSaving]   = useState(false)
  const [saved,    setSaved]    = useState(false)
  const [saveError, setSaveError] = useState('')

  // ── Load latest assessment as baseline ──
  const fetchBaseline = useCallback(async () => {
    setBaselineStatus('loading')
    try {
      const history = await assessmentApi.history()
      if (history.length > 0) {
        const latest = [...history].sort(
          (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        )[0]
        setBaseline(latest)
      }
      setBaselineStatus('ok')
    } catch {
      setBaselineStatus('error')
    }
  }, [])

  useEffect(() => { fetchBaseline() }, [fetchBaseline])

  // ── Helper to update a single key ──
  function set<K extends keyof ScenarioState>(key: K, val: ScenarioState[K]) {
    setSc(prev => ({ ...prev, [key]: val }))
    // Reset saved state when changes are made
    setSaved(false)
    setResult(null)
    setRunError('')
  }

  // ── Run simulation ──
  async function handleRun() {
    setRunning(true)
    setRunError('')
    setSaved(false)
    try {
      const changes = buildChanges(sc)
      const req = {
        scenario_name: scenarioName,
        changes,
        // Pass baseline values so backend has inputs
        ...(baseline && {
          transport_mode:      baseline.transport  > 0 ? ('car' as TransportMode) : undefined,
          electricity_kwh:     baseline.energy     > 0 ? baseline.energy / 0.82 : undefined,
          distance_km:         baseline.transport  > 0 ? baseline.transport / 0.192 : undefined,
          diet_type:           'mixed' as DietType,
          recycling_score:     2,
          plastic_usage_score: 3,
          household_size:      1,
        }),
      }
      const res = await simulatorApi.run(req)
      setResult(res)
    } catch (err) {
      setRunError(err instanceof Error ? err.message : 'Simulation failed')
    } finally {
      setRunning(false)
    }
  }

  // ── Save scenario ──
  async function handleSave() {
    if (!result) return
    setSaving(true)
    setSaveError('')
    try {
      await simulatorApi.save({
        scenario_name:        result.scenario_name,
        current_emission:     result.current_emission,
        projected_emission:   result.projected_emission,
        carbon_saved:         result.carbon_saved,
        reduction_percentage: result.reduction_percentage,
        simulation_data:      result.simulation_data,
      })
      setSaved(true)
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  // ── Chart data ──
  const chartData = result
    ? [
        {
          category: 'Transport',
          Current:   result.simulation_data.current.transport,
          Projected: result.simulation_data.projected.transport,
        },
        {
          category: 'Energy',
          Current:   result.simulation_data.current.energy,
          Projected: result.simulation_data.projected.energy,
        },
        {
          category: 'Food',
          Current:   result.simulation_data.current.food,
          Projected: result.simulation_data.projected.food,
        },
        {
          category: 'Waste',
          Current:   result.simulation_data.current.waste,
          Projected: result.simulation_data.projected.waste,
        },
      ]
    : []

  const anyActive = sc.transportActive || sc.energyActive || sc.foodActive || sc.wasteActive
  const col = result ? reductionColor(result.reduction_percentage) : null
  const annualSaved = result ? result.carbon_saved * 12 : 0

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950 p-4 sm:p-6 lg:p-8">
      {/* Background orbs */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-96 h-96 rounded-full bg-emerald-500/5 blur-3xl" />
        <div className="absolute bottom-0 left-0 w-80 h-80 rounded-full bg-emerald-700/5 blur-3xl" />
      </div>

      <div className="relative max-w-6xl mx-auto">

        {/* ── Header ── */}
        <div className="flex items-center justify-between gap-4 mb-8 flex-wrap">
          <div>
            <button
              onClick={() => navigate('/dashboard')}
              className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-300 mb-3 transition-colors"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Dashboard
            </button>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500/20 to-emerald-600/10
                border border-emerald-500/30 flex items-center justify-center">
                <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-100">What-If Simulator</h1>
                <p className="text-sm text-slate-400">
                  {baseline
                    ? `Baseline: ${baseline.total_emission.toFixed(1)} kg CO₂e / month`
                    : baselineStatus === 'loading'
                      ? 'Loading baseline…'
                      : 'No assessment found — results use zero baseline'}
                </p>
              </div>
            </div>
          </div>

          <button
            id="view-history-btn"
            onClick={() => navigate('/simulator/history')}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium
              text-slate-300 border border-slate-700 hover:border-slate-500 hover:text-white
              transition-all duration-200"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            View History
          </button>
        </div>

        {/* ── Two-column layout ── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* ════════════════════ LEFT — Scenario Builder ════════════════════ */}
          <div className="space-y-4">
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-5">
              <h2 className="text-base font-semibold text-slate-100 mb-1">Scenario Builder</h2>
              <p className="text-xs text-slate-500 mb-5">
                Toggle changes and tune the knobs, then run the simulation.
              </p>

              {/* Scenario name */}
              <div className="mb-5">
                <SectionLabel>Scenario name</SectionLabel>
                <input
                  id="scenario-name-input"
                  type="text"
                  value={scenarioName}
                  onChange={e => setScenarioName(e.target.value)}
                  placeholder="e.g. Switch to public transport"
                  className="w-full bg-slate-900/60 border border-slate-700 rounded-xl px-3 py-2
                    text-sm text-slate-100 placeholder-slate-600
                    focus:outline-none focus:ring-1 focus:ring-emerald-500/60 focus:border-emerald-500/60
                    transition-colors"
                />
              </div>

              {/* ── Transport ── */}
              <SectionLabel>🚗 Transport</SectionLabel>
              <ToggleCard
                id="toggle-transport"
                emoji="🚗"
                title="Switch transport mode"
                subtitle={sc.transportActive ? `→ ${sc.newMode}` : 'Swap your primary vehicle'}
                active={sc.transportActive}
                onClick={() => set('transportActive', !sc.transportActive)}
              >
                <div className="mt-3">
                  <p className="text-xs text-slate-500 mb-2">New mode</p>
                  <div className="grid grid-cols-3 gap-2">
                    {TRANSPORT_OPTIONS.map(opt => (
                      <button
                        key={opt.value}
                        type="button"
                        onClick={() => set('newMode', opt.value)}
                        className={`flex flex-col items-center gap-1 py-2 rounded-xl text-xs font-medium
                          transition-all duration-150 border
                          ${sc.newMode === opt.value
                            ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300'
                            : 'bg-slate-800/60 border-slate-700 text-slate-400 hover:border-slate-500'
                          }`}
                      >
                        <span className="text-base">{opt.emoji}</span>
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </div>
              </ToggleCard>

              <div className="mt-3" />

              {/* ── Energy ── */}
              <SectionLabel>⚡ Energy</SectionLabel>
              <ToggleCard
                id="toggle-energy"
                emoji="⚡"
                title="Reduce energy consumption"
                subtitle={sc.energyActive
                  ? [
                      sc.electricityReductionPct > 0 && `−${sc.electricityReductionPct}% electricity`,
                      sc.reducedAc && 'No AC',
                      sc.solarAdoption && 'Solar ON',
                    ].filter(Boolean).join(' · ') || 'Configure below'
                  : 'Cut electricity, AC or add solar'}
                active={sc.energyActive}
                onClick={() => set('energyActive', !sc.energyActive)}
              >
                <SliderRow
                  label="Electricity reduction"
                  value={sc.electricityReductionPct}
                  min={0} max={100} step={5} unit="%"
                  onChange={v => set('electricityReductionPct', v)}
                />
                <div className="flex gap-3 mt-3">
                  {/* Reduced AC */}
                  <button
                    type="button"
                    onClick={() => set('reducedAc', !sc.reducedAc)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium
                      border transition-all duration-150
                      ${sc.reducedAc
                        ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300'
                        : 'bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-500'
                      }`}
                  >
                    <span>❄️</span> No AC
                  </button>
                  {/* Solar */}
                  <button
                    type="button"
                    onClick={() => set('solarAdoption', !sc.solarAdoption)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium
                      border transition-all duration-150
                      ${sc.solarAdoption
                        ? 'bg-amber-500/20 border-amber-500/40 text-amber-300'
                        : 'bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-500'
                      }`}
                  >
                    <span>☀️</span> Solar panels
                  </button>
                </div>
              </ToggleCard>

              <div className="mt-3" />

              {/* ── Food ── */}
              <SectionLabel>🥗 Food</SectionLabel>
              <ToggleCard
                id="toggle-food"
                emoji="🥗"
                title="Change diet type"
                subtitle={sc.foodActive ? `→ ${sc.newDietType.replace('_', ' ')}` : 'Switch your eating habits'}
                active={sc.foodActive}
                onClick={() => set('foodActive', !sc.foodActive)}
              >
                <div className="flex gap-2 mt-3">
                  {DIET_OPTIONS.map(opt => (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => set('newDietType', opt.value)}
                      className={`flex-1 flex flex-col items-center gap-1 py-2 rounded-xl text-xs font-medium
                        border transition-all duration-150
                        ${sc.newDietType === opt.value
                          ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300'
                          : 'bg-slate-800/60 border-slate-700 text-slate-400 hover:border-slate-500'
                        }`}
                    >
                      <span className="text-base">{opt.emoji}</span>
                      {opt.label}
                    </button>
                  ))}
                </div>
              </ToggleCard>

              <div className="mt-3" />

              {/* ── Waste ── */}
              <SectionLabel>🗑️ Waste</SectionLabel>
              <ToggleCard
                id="toggle-waste"
                emoji="🗑️"
                title="Improve waste habits"
                subtitle={sc.wasteActive
                  ? `Recycle +${sc.recyclingImprovement} · Plastic −${sc.plasticReduction}`
                  : 'Recycle more, use less plastic'}
                active={sc.wasteActive}
                onClick={() => set('wasteActive', !sc.wasteActive)}
              >
                <SliderRow
                  label="Recycling improvement"
                  value={sc.recyclingImprovement}
                  min={0} max={5} unit=" pts"
                  onChange={v => set('recyclingImprovement', v)}
                />
                <SliderRow
                  label="Plastic reduction"
                  value={sc.plasticReduction}
                  min={0} max={5} unit=" pts"
                  onChange={v => set('plasticReduction', v)}
                />
              </ToggleCard>

              {/* Run button */}
              <button
                id="run-simulation-btn"
                type="button"
                disabled={!anyActive || running}
                onClick={handleRun}
                className="mt-5 w-full flex items-center justify-center gap-2 py-3 rounded-xl
                  text-sm font-semibold text-white transition-all duration-200
                  disabled:opacity-40 disabled:cursor-not-allowed
                  bg-gradient-to-r from-emerald-500 to-emerald-600
                  hover:from-emerald-400 hover:to-emerald-500
                  shadow-lg shadow-emerald-500/20 hover:shadow-emerald-500/35"
              >
                {running
                  ? <><Spinner size="sm" /><span>Running…</span></>
                  : <>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                      Run Simulation
                    </>
                }
              </button>
              {!anyActive && (
                <p className="text-center text-xs text-slate-600 mt-2">
                  Toggle at least one change category above
                </p>
              )}
              {runError && (
                <p className="text-xs text-rose-400 text-center mt-2">{runError}</p>
              )}
            </div>
          </div>

          {/* ════════════════════ RIGHT — Results Panel ════════════════════ */}
          <div className="space-y-4">
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-5">
              <div className="flex items-center justify-between mb-1">
                <h2 className="text-base font-semibold text-slate-100">Simulation Results</h2>
                {result && (
                  <span className="text-xs text-slate-500">{result.scenario_name}</span>
                )}
              </div>
              <p className="text-xs text-slate-500 mb-5">
                Monthly emission: current vs projected
              </p>

              {!result && <ResultsPlaceholder />}

              {result && (
                <div className="space-y-5 animate-fade-in">

                  {/* ── Headline stats ── */}
                  <div className="grid grid-cols-2 gap-3">
                    {/* Current */}
                    <div className="bg-slate-900/50 border border-slate-700/50 rounded-xl p-4 text-center">
                      <p className="text-xs text-slate-500 mb-1">Current</p>
                      <p className="text-2xl font-bold text-slate-100 tabular-nums">
                        {result.current_emission.toFixed(1)}
                      </p>
                      <p className="text-xs text-slate-500">kg CO₂e / mo</p>
                    </div>
                    {/* Projected */}
                    <div className={`border rounded-xl p-4 text-center ${col?.bg} ${col?.ring} ring-1`}>
                      <p className="text-xs text-slate-500 mb-1">Projected</p>
                      <p className={`text-2xl font-bold tabular-nums ${col?.text}`}>
                        {result.projected_emission.toFixed(1)}
                      </p>
                      <p className="text-xs text-slate-500">kg CO₂e / mo</p>
                    </div>
                  </div>

                  {/* ── Reduction badges ── */}
                  <div className="grid grid-cols-3 gap-3">
                    <div className="bg-slate-900/50 border border-slate-700/40 rounded-xl p-3 text-center">
                      <p className={`text-xl font-bold tabular-nums ${col?.text}`}>
                        {result.carbon_saved >= 0 ? '−' : '+'}
                        {Math.abs(result.carbon_saved).toFixed(1)}
                      </p>
                      <p className="text-xs text-slate-500 mt-0.5">kg saved/mo</p>
                    </div>
                    <div className={`border rounded-xl p-3 text-center ${col?.bg} ring-1 ${col?.ring}`}>
                      <p className={`text-xl font-bold tabular-nums ${col?.text}`}>
                        {result.reduction_percentage >= 0 ? '−' : '+'}
                        {Math.abs(result.reduction_percentage).toFixed(1)}%
                      </p>
                      <p className="text-xs text-slate-500 mt-0.5">reduction</p>
                    </div>
                    <div className="bg-slate-900/50 border border-slate-700/40 rounded-xl p-3 text-center">
                      <p className="text-xl font-bold tabular-nums text-emerald-400">
                        {annualSaved >= 0 ? '−' : '+'}
                        {Math.abs(annualSaved).toFixed(0)}
                      </p>
                      <p className="text-xs text-slate-500 mt-0.5">kg/year est.</p>
                    </div>
                  </div>

                  {/* ── Bar chart ── */}
                  <div>
                    <SectionLabel>Emission breakdown — current vs projected</SectionLabel>
                    <div className="h-52">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                          data={chartData}
                          barCategoryGap="30%"
                          barGap={4}
                          margin={{ top: 4, right: 4, bottom: 0, left: -16 }}
                        >
                          <CartesianGrid
                            strokeDasharray="3 3"
                            stroke="#1e293b"
                            vertical={false}
                          />
                          <XAxis
                            dataKey="category"
                            tick={{ fill: '#64748b', fontSize: 11 }}
                            axisLine={false}
                            tickLine={false}
                          />
                          <YAxis
                            tick={{ fill: '#64748b', fontSize: 11 }}
                            axisLine={false}
                            tickLine={false}
                            tickFormatter={v => `${v}`}
                          />
                          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
                          <Legend
                            wrapperStyle={{ fontSize: 11, color: '#64748b', paddingTop: 8 }}
                          />
                          <Bar dataKey="Current" radius={[4,4,0,0]} maxBarSize={28}>
                            {chartData.map((_, i) => (
                              <Cell key={i} fill="#475569" />
                            ))}
                          </Bar>
                          <Bar dataKey="Projected" radius={[4,4,0,0]} maxBarSize={28}>
                            {chartData.map((_, i) => (
                              <Cell key={i} fill="#10b981" />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  {/* ── Changes applied ── */}
                  {Object.keys(result.simulation_data.changes_applied).length > 0 && (
                    <div>
                      <SectionLabel>Changes applied</SectionLabel>
                      <div className="space-y-1.5">
                        {Object.entries(result.simulation_data.changes_applied).map(([key, val]) => (
                          <div
                            key={key}
                            className="flex items-center justify-between text-xs py-1.5 px-3
                              bg-slate-900/50 border border-slate-700/40 rounded-lg"
                          >
                            <span className="text-slate-500 capitalize">
                              {key.replace(/_/g, ' ')}
                            </span>
                            <span className="text-slate-300 font-medium">{val}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* ── Save / History actions ── */}
                  <div className="flex gap-3 pt-1">
                    <button
                      id="save-scenario-btn"
                      type="button"
                      disabled={saving || saved}
                      onClick={handleSave}
                      className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl
                        text-sm font-semibold transition-all duration-200
                        disabled:opacity-50 disabled:cursor-not-allowed
                        bg-emerald-500/15 border border-emerald-500/30 text-emerald-300
                        hover:bg-emerald-500/25 hover:border-emerald-500/50"
                    >
                      {saving ? (
                        <><Spinner size="sm" /><span>Saving…</span></>
                      ) : saved ? (
                        <><span>✓</span><span>Saved!</span></>
                      ) : (
                        <>
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                              d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
                          </svg>
                          Save Scenario
                        </>
                      )}
                    </button>

                    <button
                      id="view-history-results-btn"
                      type="button"
                      onClick={() => navigate('/simulator/history')}
                      className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium
                        text-slate-400 border border-slate-700 hover:border-slate-500 hover:text-slate-200
                        transition-all duration-200"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                          d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      History
                    </button>
                  </div>

                  {saveError && (
                    <p className="text-xs text-rose-400 text-center">{saveError}</p>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
