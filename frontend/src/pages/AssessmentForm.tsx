/**
 * AssessmentForm.tsx — Carbon Horizon 4-step footprint wizard
 *
 * Step 1: Transport   — transport_mode, distance_km
 * Step 2: Energy      — electricity_kwh, ac_hours, lpg_usage, solar_usage
 * Step 3: Food &amp; Waste — diet_type, recycling_score, plastic_usage_score, household_size
 * Step 4: Review      — read-only summary + submit
 *
 * Validation: Zod per-step schemas, React Hook Form
 * On success: navigate to /dashboard with AssessmentResult in location.state
 */
import { useState, useCallback } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useNavigate } from 'react-router-dom'
import { assessmentApi, type AssessmentResult } from '@/api/assessment'

// ─── Zod schemas (one per step) ──────────────────────────────────────────────

const transportSchema = z.object({
  transport_mode: z.enum(
    ['car', 'motorcycle', 'bus', 'train', 'flight', 'bicycle'],
    { error: 'Please select a transport mode' },
  ),
  distance_km: z
    .number({ error: 'Enter a valid distance' })
    .min(0, 'Distance must be ≥ 0')
    .max(100_000, 'Distance seems too large'),
})

const energySchema = z.object({
  electricity_kwh: z
    .number({ error: 'Enter a valid number' })
    .min(0, 'Must be ≥ 0')
    .max(10_000, 'Value seems too large'),
  ac_hours: z
    .number({ error: 'Enter a valid number' })
    .min(0, 'Must be ≥ 0')
    .max(744, 'Max 744 hrs/month'),
  lpg_usage: z
    .number({ error: 'Enter a valid number' })
    .min(0, 'Must be ≥ 0')
    .max(500, 'Value seems too large'),
  solar_usage: z.boolean(),
})

const foodWasteSchema = z.object({
  diet_type: z.enum(['vegetarian', 'mixed', 'non_vegetarian'], {
    error: 'Please select a diet type',
  }),
  recycling_score: z
    .number({ error: 'Select a score' })
    .int()
    .min(1)
    .max(5),
  plastic_usage_score: z
    .number({ error: 'Select a score' })
    .int()
    .min(1)
    .max(5),
  household_size: z
    .number({ error: 'Enter household size' })
    .int()
    .min(1, 'At least 1 person')
    .max(20, 'Max 20 people'),
})

// Full merged schema for the Review step final submit
const fullSchema = transportSchema.merge(energySchema).merge(foodWasteSchema)
type FullFormData = z.infer<typeof fullSchema>

// ─── Step config ─────────────────────────────────────────────────────────────

const STEPS = [
  { id: 1, label: 'Transport', icon: '🚗' },
  { id: 2, label: 'Energy',    icon: '⚡' },
  { id: 3, label: 'Food & Waste', icon: '🥗' },
  { id: 4, label: 'Review',    icon: '✅' },
]

const TRANSPORT_OPTIONS = [
  { value: 'car',        label: '🚗  Car',        sub: '0.192 kg CO₂e/km' },
  { value: 'motorcycle', label: '🏍️  Motorcycle', sub: '0.113 kg CO₂e/km' },
  { value: 'bus',        label: '🚌  Bus',         sub: '0.089 kg CO₂e/km' },
  { value: 'train',      label: '🚆  Train',       sub: '0.041 kg CO₂e/km' },
  { value: 'flight',     label: '✈️  Flight',      sub: '0.255 kg CO₂e/km' },
  { value: 'bicycle',    label: '🚲  Bicycle',     sub: '0 kg CO₂e/km' },
]

const DIET_OPTIONS = [
  { value: 'vegetarian',     label: '🥦  Vegetarian',     sub: '1.7 kg CO₂e/day' },
  { value: 'mixed',          label: '🥗  Mixed',           sub: '2.5 kg CO₂e/day' },
  { value: 'non_vegetarian', label: '🍖  Non-Vegetarian',  sub: '3.3 kg CO₂e/day' },
]

// ─── Small helpers ────────────────────────────────────────────────────────────

function ScoreButton({
  value,
  selected,
  onClick,
  lowLabel,
  highLabel,
}: {
  value: number
  selected: boolean
  onClick: () => void
  lowLabel?: string
  highLabel?: string
}) {
  const isLow  = value <= 2
  const isHigh = value >= 4

  return (
    <button
      type="button"
      onClick={onClick}
      title={`Score ${value}${lowLabel && value === 1 ? ` — ${lowLabel}` : highLabel && value === 5 ? ` — ${highLabel}` : ''}`}
      className={[
        'w-10 h-10 rounded-xl text-sm font-bold border-2 transition-all duration-200',
        selected
          ? isLow
            ? 'bg-emerald-500 border-emerald-400 text-white shadow-lg shadow-emerald-500/30 scale-110'
            : isHigh
            ? 'bg-rose-500 border-rose-400 text-white shadow-lg shadow-rose-500/30 scale-110'
            : 'bg-amber-500 border-amber-400 text-white shadow-lg shadow-amber-500/30 scale-110'
          : 'bg-slate-800/60 border-slate-600 text-slate-400 hover:border-slate-400 hover:text-slate-200',
      ].join(' ')}
    >
      {value}
    </button>
  )
}

function FieldLabel({ children, hint }: { children: React.ReactNode; hint?: string }) {
  return (
    <label className="block text-sm font-medium text-slate-300 mb-1.5">
      {children}
      {hint && <span className="ml-1.5 text-xs text-slate-500 font-normal">{hint}</span>}
    </label>
  )
}

function NumberInput({
  id,
  value,
  onChange,
  min = 0,
  step = 1,
  placeholder = '0',
  error,
}: {
  id: string
  value: string
  onChange: (val: number) => void
  min?: number
  step?: number
  placeholder?: string
  error?: string
}) {
  return (
    <div>
      <input
        id={id}
        type="number"
        inputMode="decimal"
        min={min}
        step={step}
        placeholder={placeholder}
        value={value}
        onChange={(e) => {
          const n = parseFloat(e.target.value)
          if (!isNaN(n)) onChange(n)
          else if (e.target.value === '') onChange(0)
        }}
        className={[
          'w-full px-4 py-2.5 rounded-xl bg-slate-800/60 border text-slate-100 placeholder-slate-500 text-sm',
          'focus:outline-none focus:ring-2 focus:ring-emerald-500/70 focus:border-emerald-500 transition-all duration-200',
          error ? 'border-red-500/70' : 'border-slate-700',
        ].join(' ')}
      />
      {error && <p className="mt-1 text-xs text-red-400">{error}</p>}
    </div>
  )
}

function SelectCard({
  options,
  value,
  onChange,
  error,
}: {
  options: { value: string; label: string; sub?: string }[]
  value: string
  onChange: (v: string) => void
  error?: string
}) {
  return (
    <div>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        {options.map((opt) => {
          const active = value === opt.value
          return (
            <button
              key={opt.value}
              type="button"
              onClick={() => onChange(opt.value)}
              className={[
                'flex flex-col items-start p-3 rounded-xl border-2 text-left transition-all duration-200 group',
                active
                  ? 'border-emerald-500 bg-emerald-500/10 shadow-lg shadow-emerald-500/10'
                  : 'border-slate-700 bg-slate-800/40 hover:border-slate-500 hover:bg-slate-800/70',
              ].join(' ')}
            >
              <span className={`text-sm font-medium leading-snug ${active ? 'text-emerald-300' : 'text-slate-200'}`}>
                {opt.label}
              </span>
              {opt.sub && (
                <span className={`mt-0.5 text-xs ${active ? 'text-emerald-400/80' : 'text-slate-500'}`}>
                  {opt.sub}
                </span>
              )}
            </button>
          )
        })}
      </div>
      {error && <p className="mt-2 text-xs text-red-400">{error}</p>}
    </div>
  )
}

function Toggle({
  checked,
  onChange,
  label,
  description,
}: {
  checked: boolean
  onChange: (v: boolean) => void
  label: string
  description?: string
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className={[
        'w-full flex items-center justify-between p-4 rounded-xl border-2 transition-all duration-200',
        checked
          ? 'border-emerald-500 bg-emerald-500/10'
          : 'border-slate-700 bg-slate-800/40 hover:border-slate-500',
      ].join(' ')}
    >
      <div className="text-left">
        <p className={`text-sm font-medium ${checked ? 'text-emerald-300' : 'text-slate-200'}`}>{label}</p>
        {description && <p className="text-xs text-slate-500 mt-0.5">{description}</p>}
      </div>
      <div
        className={[
          'relative w-11 h-6 rounded-full transition-colors duration-300 flex-shrink-0',
          checked ? 'bg-emerald-500' : 'bg-slate-600',
        ].join(' ')}
      >
        <span
          className={[
            'absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-300',
            checked ? 'translate-x-5' : 'translate-x-0',
          ].join(' ')}
        />
      </div>
    </button>
  )
}

function ReviewRow({ label, value, highlight = false }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="flex justify-between items-center py-2.5 border-b border-slate-800 last:border-0">
      <span className="text-sm text-slate-400">{label}</span>
      <span className={`text-sm font-medium ${highlight ? 'text-emerald-400' : 'text-slate-200'}`}>{value}</span>
    </div>
  )
}

// ─── Spinner ─────────────────────────────────────────────────────────────────

function Spinner() {
  return (
    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  )
}

// ─── Main Component ───────────────────────────────────────────────────────────

const DEFAULT_VALUES: FullFormData = {
  transport_mode: 'car',
  distance_km: 0,
  electricity_kwh: 0,
  ac_hours: 0,
  lpg_usage: 0,
  solar_usage: false,
  diet_type: 'mixed',
  recycling_score: 3,
  plastic_usage_score: 3,
  household_size: 1,
}

// Per-step schemas for trigger() validation


export default function AssessmentForm() {
  const navigate = useNavigate()
  const [step, setStep]           = useState(1)
  const [apiError, setApiError]   = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // We use a single RHF instance with the full merged schema
  const {
    control,
    trigger,
    getValues,
    formState: { errors },
  } = useForm<FullFormData>({
    resolver: zodResolver(fullSchema),
    defaultValues: DEFAULT_VALUES,
    mode: 'onTouched',
  })

  // Local display strings for number inputs (keeps them editable as strings)
  const [numStr, setNumStr] = useState({
    distance_km:      '0',
    electricity_kwh:  '0',
    ac_hours:         '0',
    lpg_usage:        '0',
    household_size:   '1',
  })

  const updateNum = useCallback((key: keyof typeof numStr, raw: string) => {
    setNumStr((prev) => ({ ...prev, [key]: raw }))
  }, [])

  // ── Step navigation ───────────────────────────────────────────────────────

  const fieldsForStep: Record<number, (keyof FullFormData)[]> = {
    1: ['transport_mode', 'distance_km'],
    2: ['electricity_kwh', 'ac_hours', 'lpg_usage', 'solar_usage'],
    3: ['diet_type', 'recycling_score', 'plastic_usage_score', 'household_size'],
    4: [],
  }

  const goNext = async () => {
    const fields = fieldsForStep[step]
    const valid  = await trigger(fields as (keyof FullFormData)[])
    if (valid) setStep((s) => Math.min(s + 1, 4))
  }

  const goBack = () => {
    setApiError(null)
    setStep((s) => Math.max(s - 1, 1))
  }

  // ── Submit ────────────────────────────────────────────────────────────────

  const onSubmit = async () => {
    const data = getValues()
    setApiError(null)
    setIsSubmitting(true)
    try {
      const result: AssessmentResult = await assessmentApi.create({
        ...data,
        assessment_period: 'monthly',
      })
      navigate('/assessment/result', { state: { assessmentResult: result }, replace: false })
    } catch (err) {
      setApiError(err instanceof Error ? err.message : 'Submission failed. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  // ── Derived values for review ─────────────────────────────────────────────

  const vals = getValues()

  const transportLabel =
    TRANSPORT_OPTIONS.find((o) => o.value === vals.transport_mode)?.label ?? vals.transport_mode
  const dietLabel =
    DIET_OPTIONS.find((o) => o.value === vals.diet_type)?.label ?? vals.diet_type

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950 flex items-center justify-center p-4 py-10">
      {/* Background orbs */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-96 h-96 rounded-full bg-emerald-500/8 blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 rounded-full bg-emerald-700/6 blur-3xl" />
      </div>

      <div className="relative w-full max-w-xl">
        {/* Logo / Brand */}
        <div className="flex items-center gap-2.5 mb-6 justify-center">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center shadow-lg shadow-emerald-500/30">
            <svg viewBox="0 0 24 24" className="w-5 h-5 text-white fill-current">
              <path d="M17 8C8 10 5.9 16.17 3.82 21.34L5.71 22l1-2.3A4.49 4.49 0 0 0 8 20C19 20 22 3 22 3c-1 2-8 2-8 2 0 0-4 0-4 8" />
            </svg>
          </div>
          <span className="text-xl font-semibold tracking-tight text-slate-100">
            Carbon<span className="text-emerald-400">Horizon</span>
          </span>
        </div>

        {/* ── Progress bar ── */}
        <div className="mb-6">
          {/* Step labels */}
          <div className="flex justify-between mb-3">
            {STEPS.map((s) => (
              <div
                key={s.id}
                className="flex flex-col items-center gap-1"
                style={{ width: `${100 / STEPS.length}%` }}
              >
                <div
                  className={[
                    'w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold border-2 transition-all duration-300',
                    s.id < step
                      ? 'bg-emerald-500 border-emerald-400 text-white'
                      : s.id === step
                      ? 'bg-emerald-500/20 border-emerald-500 text-emerald-400 ring-4 ring-emerald-500/15'
                      : 'bg-slate-800 border-slate-700 text-slate-600',
                  ].join(' ')}
                >
                  {s.id < step ? (
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    <span>{s.icon}</span>
                  )}
                </div>
                <span
                  className={`text-xs font-medium hidden sm:block ${
                    s.id === step ? 'text-emerald-400' : s.id < step ? 'text-emerald-500/70' : 'text-slate-600'
                  }`}
                >
                  {s.label}
                </span>
              </div>
            ))}
          </div>

          {/* Progress track */}
          <div className="relative h-1.5 bg-slate-800 rounded-full overflow-hidden">
            <div
              className="absolute inset-y-0 left-0 bg-gradient-to-r from-emerald-600 to-emerald-400 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${((step - 1) / (STEPS.length - 1)) * 100}%` }}
            />
          </div>

          <p className="text-xs text-slate-500 mt-2 text-right">
            Step {step} of {STEPS.length}
          </p>
        </div>

        {/* ── Card ── */}
        <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-700/50 rounded-2xl shadow-2xl shadow-black/40 p-7">

          {/* Step 1: Transport */}
          {step === 1 && (
            <div className="space-y-5 animate-fade-in">
              <div>
                <h2 className="text-xl font-bold text-slate-100">Transport</h2>
                <p className="text-sm text-slate-400 mt-1">How do you mainly get around each month?</p>
              </div>

              <div>
                <FieldLabel>Primary transport mode</FieldLabel>
                <Controller
                  name="transport_mode"
                  control={control}
                  render={({ field }) => (
                    <SelectCard
                      options={TRANSPORT_OPTIONS}
                      value={field.value}
                      onChange={field.onChange}
                      error={errors.transport_mode?.message}
                    />
                  )}
                />
              </div>

              <div>
                <FieldLabel hint="km/month">Monthly distance</FieldLabel>
                <Controller
                  name="distance_km"
                  control={control}
                  render={({ field }) => (
                    <NumberInput
                      id="distance_km"
                      value={numStr.distance_km}
                      onChange={(v) => { field.onChange(v); updateNum('distance_km', String(v)) }}
                      step={10}
                      placeholder="e.g. 500"
                      error={errors.distance_km?.message}
                    />
                  )}
                />
              </div>
            </div>
          )}

          {/* Step 2: Energy */}
          {step === 2 && (
            <div className="space-y-5 animate-fade-in">
              <div>
                <h2 className="text-xl font-bold text-slate-100">Energy Usage</h2>
                <p className="text-sm text-slate-400 mt-1">Monthly household energy consumption.</p>
              </div>

              <div>
                <FieldLabel hint="kWh/month">Electricity consumption</FieldLabel>
                <Controller
                  name="electricity_kwh"
                  control={control}
                  render={({ field }) => (
                    <NumberInput
                      id="electricity_kwh"
                      value={numStr.electricity_kwh}
                      onChange={(v) => { field.onChange(v); updateNum('electricity_kwh', String(v)) }}
                      step={10}
                      placeholder="e.g. 200"
                      error={errors.electricity_kwh?.message}
                    />
                  )}
                />
              </div>

              <div>
                <FieldLabel hint="hours/month">AC usage</FieldLabel>
                <Controller
                  name="ac_hours"
                  control={control}
                  render={({ field }) => (
                    <NumberInput
                      id="ac_hours"
                      value={numStr.ac_hours}
                      onChange={(v) => { field.onChange(v); updateNum('ac_hours', String(v)) }}
                      step={5}
                      placeholder="e.g. 120"
                      error={errors.ac_hours?.message}
                    />
                  )}
                />
              </div>

              <div>
                <FieldLabel hint="kg/month">LPG / cooking gas</FieldLabel>
                <Controller
                  name="lpg_usage"
                  control={control}
                  render={({ field }) => (
                    <NumberInput
                      id="lpg_usage"
                      value={numStr.lpg_usage}
                      onChange={(v) => { field.onChange(v); updateNum('lpg_usage', String(v)) }}
                      step={1}
                      placeholder="e.g. 14"
                      error={errors.lpg_usage?.message}
                    />
                  )}
                />
              </div>

              <Controller
                name="solar_usage"
                control={control}
                render={({ field }) => (
                  <Toggle
                    checked={field.value}
                    onChange={field.onChange}
                    label="☀️  Solar panels installed"
                    description="Offsets 100% of grid electricity emissions"
                  />
                )}
              />
            </div>
          )}

          {/* Step 3: Food & Waste */}
          {step === 3 && (
            <div className="space-y-6 animate-fade-in">
              <div>
                <h2 className="text-xl font-bold text-slate-100">Food &amp; Waste</h2>
                <p className="text-sm text-slate-400 mt-1">Your diet and waste habits per month.</p>
              </div>

              <div>
                <FieldLabel>Diet type</FieldLabel>
                <Controller
                  name="diet_type"
                  control={control}
                  render={({ field }) => (
                    <SelectCard
                      options={DIET_OPTIONS}
                      value={field.value}
                      onChange={field.onChange}
                      error={errors.diet_type?.message}
                    />
                  )}
                />
              </div>

              {/* Recycling score */}
              <div>
                <FieldLabel>
                  Recycling habit score
                  <span className="ml-1.5 text-xs text-slate-500 font-normal">1 = never, 5 = always</span>
                </FieldLabel>
                <Controller
                  name="recycling_score"
                  control={control}
                  render={({ field }) => (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-emerald-400 w-12">Never</span>
                        {[1, 2, 3, 4, 5].map((v) => (
                          <ScoreButton
                            key={v}
                            value={v}
                            selected={field.value === v}
                            onClick={() => field.onChange(v)}
                            lowLabel="Never"
                            highLabel="Always"
                          />
                        ))}
                        <span className="text-xs text-emerald-400 w-12 text-right">Always</span>
                      </div>
                      {errors.recycling_score && (
                        <p className="text-xs text-red-400">{errors.recycling_score.message}</p>
                      )}
                    </div>
                  )}
                />
              </div>

              {/* Plastic score */}
              <div>
                <FieldLabel>
                  Plastic usage score
                  <span className="ml-1.5 text-xs text-slate-500 font-normal">1 = minimal, 5 = heavy</span>
                </FieldLabel>
                <Controller
                  name="plastic_usage_score"
                  control={control}
                  render={({ field }) => (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-emerald-400 w-12">Low</span>
                        {[1, 2, 3, 4, 5].map((v) => (
                          <ScoreButton
                            key={v}
                            value={v}
                            selected={field.value === v}
                            onClick={() => field.onChange(v)}
                            lowLabel="Minimal"
                            highLabel="Heavy"
                          />
                        ))}
                        <span className="text-xs text-rose-400 w-12 text-right">High</span>
                      </div>
                      {errors.plastic_usage_score && (
                        <p className="text-xs text-red-400">{errors.plastic_usage_score.message}</p>
                      )}
                    </div>
                  )}
                />
              </div>

              <div>
                <FieldLabel hint="people sharing the home">Household size</FieldLabel>
                <Controller
                  name="household_size"
                  control={control}
                  render={({ field }) => (
                    <NumberInput
                      id="household_size"
                      value={numStr.household_size}
                      onChange={(v) => { field.onChange(v); updateNum('household_size', String(v)) }}
                      min={1}
                      step={1}
                      placeholder="e.g. 4"
                      error={errors.household_size?.message}
                    />
                  )}
                />
              </div>
            </div>
          )}

          {/* Step 4: Review */}
          {step === 4 && (
            <div className="space-y-5 animate-fade-in">
              <div>
                <h2 className="text-xl font-bold text-slate-100">Review &amp; Submit</h2>
                <p className="text-sm text-slate-400 mt-1">
                  Check your inputs below. Go back to edit any step.
                </p>
              </div>

              {/* Transport summary */}
              <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-base">🚗</span>
                  <h3 className="text-sm font-semibold text-emerald-400 uppercase tracking-wide">Transport</h3>
                </div>
                <ReviewRow label="Mode" value={transportLabel} />
                <ReviewRow label="Monthly distance" value={`${vals.distance_km.toLocaleString()} km`} />
              </div>

              {/* Energy summary */}
              <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-base">⚡</span>
                  <h3 className="text-sm font-semibold text-emerald-400 uppercase tracking-wide">Energy</h3>
                </div>
                <ReviewRow label="Electricity" value={`${vals.electricity_kwh} kWh/month`} />
                <ReviewRow label="AC usage" value={`${vals.ac_hours} hrs/month`} />
                <ReviewRow label="LPG / gas" value={`${vals.lpg_usage} kg/month`} />
                <ReviewRow label="Solar panels" value={vals.solar_usage ? '✅  Yes' : '❌  No'} />
              </div>

              {/* Food & Waste summary */}
              <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-base">🥗</span>
                  <h3 className="text-sm font-semibold text-emerald-400 uppercase tracking-wide">Food &amp; Waste</h3>
                </div>
                <ReviewRow label="Diet" value={dietLabel} />
                <ReviewRow label="Recycling score" value={`${vals.recycling_score} / 5`} />
                <ReviewRow label="Plastic usage" value={`${vals.plastic_usage_score} / 5`} />
                <ReviewRow label="Household size" value={`${vals.household_size} person${vals.household_size !== 1 ? 's' : ''}`} />
              </div>

              {/* Period badge */}
              <div className="flex items-center gap-2 px-4 py-2.5 bg-emerald-500/10 border border-emerald-500/30 rounded-xl">
                <svg className="w-4 h-4 text-emerald-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <span className="text-sm text-emerald-300 font-medium">
                  Assessment period: <span className="text-emerald-200">Monthly</span>
                </span>
              </div>

              {/* API error */}
              {apiError && (
                <div className="flex items-start gap-2.5 p-3.5 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
                  <svg className="w-4 h-4 mt-0.5 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  <span>{apiError}</span>
                </div>
              )}
            </div>
          )}

          {/* ── Navigation buttons ── */}
          <div className={`flex gap-3 mt-7 ${step === 1 ? 'justify-end' : 'justify-between'}`}>
            {step > 1 && (
              <button
                type="button"
                onClick={goBack}
                disabled={isSubmitting}
                className="flex items-center gap-1.5 px-5 py-2.5 rounded-xl text-sm font-medium text-slate-300 border border-slate-700 hover:border-slate-500 hover:text-slate-100 disabled:opacity-50 transition-all duration-200"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Back
              </button>
            )}

            {step < 4 ? (
              <button
                type="button"
                id={`step-${step}-next`}
                onClick={goNext}
                className="flex items-center gap-1.5 px-6 py-2.5 rounded-xl text-sm font-semibold text-white bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-400 hover:to-emerald-500 shadow-lg shadow-emerald-500/25 hover:shadow-emerald-500/40 transition-all duration-200"
              >
                Next
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            ) : (
              <button
                type="button"
                id="submit-assessment"
                onClick={onSubmit}
                disabled={isSubmitting}
                className="flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-semibold text-white bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-400 hover:to-emerald-500 shadow-lg shadow-emerald-500/25 hover:shadow-emerald-500/40 disabled:opacity-60 disabled:cursor-not-allowed transition-all duration-200"
              >
                {isSubmitting ? (
                  <>
                    <Spinner />
                    Calculating…
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Calculate my footprint
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
