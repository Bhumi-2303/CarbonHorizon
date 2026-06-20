import { useState } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useNavigate } from 'react-router-dom'
import { assessmentApi } from '@/api/assessment'
import { useAuth } from '@/context/AuthContext'
import { 
  Car, Zap, Salad, Droplets, Trash2, 
  Home, Laptop, ShoppingBag, Briefcase, MapPin, Leaf, CheckCircle
} from 'lucide-react'

// ─── Zod schemas ─────────────────────────────────────────────────────────────
const formSchema = z.object({
  // Step 1: Transport
  transport_mode: z.enum(['car', 'motorcycle', 'bus', 'train', 'flight', 'bicycle'], { error: 'Required' }),
  distance_km: z.number().min(0),
  vehicle_type: z.string().optional(),
  fuel_type: z.string().optional(),
  trips_per_week: z.number().min(0).optional(),
  public_transport_usage: z.string().optional(),
  carpooling_frequency: z.string().optional(),
  air_travel_frequency: z.string().optional(),
  train_travel_frequency: z.string().optional(),
  walking_cycling_hours: z.number().min(0).optional(),

  // Step 2: Energy
  electricity_kwh: z.number().min(0),
  ac_hours: z.number().min(0),
  lpg_usage: z.number().min(0),
  solar_usage: z.boolean(),
  energy_efficiency_rating: z.string().optional(),
  heating_type: z.string().optional(),

  // Step 3: Food
  diet_type: z.enum(['vegetarian', 'mixed', 'non_vegetarian'], { error: 'Required' }),
  household_size: z.number().min(1),
  local_food_frequency: z.string().optional(),
  food_waste_percentage: z.number().min(0).max(100).optional(),

  // Step 4: Water
  daily_water_liters: z.number().min(0).optional(),
  shower_duration_minutes: z.number().min(0).optional(),
  water_heating_type: z.string().optional(),

  // Step 5: Waste
  recycling_score: z.number().min(1).max(5),
  plastic_usage_score: z.number().min(1).max(5),
  composting_frequency: z.string().optional(),
  ewaste_disposal_method: z.string().optional(),

  // Step 6: Housing
  house_size_sqm: z.number().min(0).optional(),
  home_insulation_level: z.string().optional(),

  // Step 7: Digital
  screen_time_hours: z.number().min(0).optional(),
  streaming_hours: z.number().min(0).optional(),
  gaming_hours: z.number().min(0).optional(),

  // Step 8: Shopping
  new_clothes_monthly: z.number().min(0).optional(),
  second_hand_purchases: z.string().optional(),
  electronics_purchases_yearly: z.number().min(0).optional(),

  // Step 9: Occupation
  commute_days_per_week: z.number().min(0).optional(),
  remote_work_percentage: z.number().min(0).max(100).optional(),

  // Step 10: Geographic
  assessment_country: z.string().optional(),
  assessment_state: z.string().optional(),
  assessment_city: z.string().optional(),

  // Step 11: Offsets
  composting_active: z.boolean().optional(),
  tree_planting_count: z.number().min(0).optional(),
  reusable_products_usage: z.string().optional(),
  green_transport_choices: z.boolean().optional(),
})

type FullFormData = z.infer<typeof formSchema>

const DEFAULT_VALUES: Partial<FullFormData> = {
  transport_mode: 'car', distance_km: 0,
  electricity_kwh: 0, ac_hours: 0, lpg_usage: 0, solar_usage: false,
  diet_type: 'mixed', household_size: 1,
  recycling_score: 3, plastic_usage_score: 3,
}

// ─── Constants ─────────────────────────────────────────────────────────────
const STEPS = [
  { id: 1, label: 'Transport', icon: <Car className="w-4 h-4 text-[#2ECC71]" /> },
  { id: 2, label: 'Energy',    icon: <Zap className="w-4 h-4 text-[#2ECC71]" /> },
  { id: 3, label: 'Food',      icon: <Salad className="w-4 h-4 text-[#2ECC71]" /> },
  { id: 4, label: 'Water',     icon: <Droplets className="w-4 h-4 text-[#2ECC71]" /> },
  { id: 5, label: 'Waste',     icon: <Trash2 className="w-4 h-4 text-[#2ECC71]" /> },
  { id: 6, label: 'Housing',   icon: <Home className="w-4 h-4 text-[#2ECC71]" /> },
  { id: 7, label: 'Digital',   icon: <Laptop className="w-4 h-4 text-[#2ECC71]" /> },
  { id: 8, label: 'Shopping',  icon: <ShoppingBag className="w-4 h-4 text-[#2ECC71]" /> },
  { id: 9, label: 'Lifestyle', icon: <Briefcase className="w-4 h-4 text-[#2ECC71]" /> },
  { id: 10, label: 'Location', icon: <MapPin className="w-4 h-4 text-[#2ECC71]" /> },
  { id: 11, label: 'Offsets',  icon: <Leaf className="w-4 h-4 text-[#2ECC71]" /> },
  { id: 12, label: 'Review',   icon: <CheckCircle className="w-4 h-4 text-[#2ECC71]" /> },
]

const COUNTRIES = ['India', 'United States', 'United Kingdom', 'Germany', 'France', 'Australia', 'Canada']

// ─── Small helpers ─────────────────────────────────────────────────────────

function FieldLabel({ children, hint }: { children: React.ReactNode; hint?: string }) {
  return (
    <label className="block text-sm font-medium text-slate-300 mb-1.5">
      {children}
      {hint && <span className="ml-1.5 text-xs text-muted font-normal">{hint}</span>}
    </label>
  )
}

function NumberInput({ id, value, onChange, min = 0, max, step = 1, placeholder = '0' }: any) {
  return (
    <input
      id={id} type="number" inputMode="decimal" min={min} max={max} step={step}
      placeholder={placeholder} value={value ?? ''}
      onChange={(e) => {
        const n = parseFloat(e.target.value)
        if (!isNaN(n)) onChange(n)
        else if (e.target.value === '') onChange(undefined)
      }}
      className="w-full px-4 py-2.5 rounded-xl bg-deep-ocean/60 border border-slate-700 text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-earth-green/70 focus:border-earth-green"
    />
  )
}

function TextInput({ id, value, onChange, placeholder, 'aria-label': ariaLabel }: any) {
  return (
    <input
      id={id} type="text" placeholder={placeholder} value={value || ''}
      onChange={(e) => onChange(e.target.value)}
      aria-label={ariaLabel || placeholder}
      className="w-full px-4 py-2.5 rounded-xl bg-deep-ocean/60 border border-slate-700 text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-earth-green/70 focus:border-earth-green"
    />
  )
}

function SelectCard({ options, value, onChange }: any) {
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
      {options.map((opt: any) => {
        const active = value === opt.value
        return (
          <button
            key={opt.value} type="button" onClick={() => onChange(opt.value)}
            className={`flex flex-col items-start p-3 rounded-xl border-2 text-left transition-all ${
              active ? 'border-earth-green bg-earth-green/10' : 'border-slate-700 bg-deep-ocean/40'
            }`}
          >
            <span className={`text-sm font-medium ${active ? 'text-emerald-300' : 'text-slate-200'}`}>
              {opt.label}
            </span>
          </button>
        )
      })}
    </div>
  )
}

function Toggle({ checked, onChange, label, description }: any) {
  return (
    <button
      type="button" role="switch" aria-checked={checked} onClick={() => onChange(!checked)}
      className={`w-full flex items-center justify-between p-4 rounded-xl border-2 transition-all ${checked ? 'border-earth-green bg-earth-green/10' : 'border-slate-700 bg-deep-ocean/40'}`}
    >
      <div className="text-left">
        <p className={`text-sm font-medium ${checked ? 'text-emerald-300' : 'text-slate-200'}`}>{label}</p>
        {description && <p className="text-xs text-muted mt-0.5">{description}</p>}
      </div>
      <div className={`relative w-11 h-6 rounded-full flex-shrink-0 ${checked ? 'bg-earth-green' : 'bg-slate-600'}`}>
        <span className={`absolute top-0.5 left-0.5 w-5 h-5 bg-deep-ocean rounded-full transition-transform ${checked ? 'translate-x-5' : 'translate-x-0'}`} />
      </div>
    </button>
  )
}

// ─── Main Component ────────────────────────────────────────────────────────

export default function AssessmentForm() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [step, setStep] = useState(1)
  const [apiError, setApiError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const { control, getValues, trigger } = useForm<FullFormData>({
    resolver: zodResolver(formSchema),
    defaultValues: DEFAULT_VALUES as FullFormData,
    mode: 'onTouched',
  })

  // Grouped Fields for Validation (Basic required fields only)
  const fieldsForStep: Record<number, (keyof FullFormData)[]> = {
    1: ['transport_mode', 'distance_km'],
    2: ['electricity_kwh', 'ac_hours', 'lpg_usage', 'solar_usage'],
    3: ['diet_type', 'household_size'],
    4: [], 5: ['recycling_score', 'plastic_usage_score'], 6: [], 7: [], 8: [], 9: [], 10: [], 11: [], 12: []
  }

  const goNext = async () => {
    const fields = fieldsForStep[step]
    const valid = fields.length === 0 ? true : await trigger(fields)
    if (valid) setStep((s) => Math.min(s + 1, STEPS.length))
  }

  const goBack = () => setStep((s) => Math.max(s - 1, 1))

  const onSubmit = async () => {
    const data = getValues()
    setApiError(null)
    setIsSubmitting(true)
    try {
      const result = await assessmentApi.create({ ...data, assessment_period: 'monthly' })
      navigate('/assessment/result', { state: { assessmentResult: result }, replace: true })
    } catch (err) {
      setApiError(err instanceof Error ? err.message : 'Submission failed.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950 flex items-center justify-center p-4 py-10">
      <div className="relative w-full max-w-2xl">
        {/* Progress Header */}
        <div className="mb-6 flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
          {STEPS.map((s) => (
            <div key={s.id} className="flex flex-col items-center min-w-[60px] gap-1 opacity-80" style={s.id === step ? { opacity: 1 } : {}}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center transition-all ${
                s.id < step ? 'bg-earth-green text-white' : s.id === step ? 'bg-earth-green/20 ring-2 ring-earth-green text-earth-green' : 'bg-deep-ocean text-muted'
              }`}>
                {s.icon}
              </div>
              <span className="text-[10px] font-medium tracking-wide uppercase">{s.label}</span>
            </div>
          ))}
        </div>

        <div className="bg-deep-ocean/80 backdrop-blur-xl border border-slate-700/50 rounded-2xl shadow-2xl p-6 md:p-8">
          
          {/* STEP 1 */}
          {step === 1 && (
            <div className="space-y-5 animate-fade-in">
              <h2 className="text-xl font-bold text-slate-100">Transport</h2>
              <div>
                <FieldLabel>Primary mode</FieldLabel>
                <Controller name="transport_mode" control={control} render={({ field }) => (
                  <SelectCard options={[
                    { value: 'car', label: 'Car' }, { value: 'motorcycle', label: 'Motorcycle' },
                    { value: 'bus', label: 'Bus' }, { value: 'train', label: 'Train' },
                    { value: 'flight', label: 'Flight' }, { value: 'bicycle', label: 'Bicycle' },
                  ]} value={field.value} onChange={field.onChange} />
                )} />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <FieldLabel hint="km/month">Monthly distance</FieldLabel>
                  <Controller name="distance_km" control={control} render={({ field }) => (
                    <NumberInput id="distance_km" {...field} />
                  )} />
                </div>
                <div>
                  <FieldLabel hint="Optional">Trips per week</FieldLabel>
                  <Controller name="trips_per_week" control={control} render={({ field }) => (
                    <NumberInput id="trips_per_week" {...field} />
                  )} />
                </div>
              </div>
            </div>
          )}

          {/* STEP 2 */}
          {step === 2 && (
            <div className="space-y-5 animate-fade-in">
              <h2 className="text-xl font-bold text-slate-100">Energy Usage</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <FieldLabel hint="kWh/month">Electricity</FieldLabel>
                  <Controller name="electricity_kwh" control={control} render={({ field }) => (
                    <NumberInput id="electricity_kwh" {...field} />
                  )} />
                </div>
                <div>
                  <FieldLabel hint="hours/month">AC usage</FieldLabel>
                  <Controller name="ac_hours" control={control} render={({ field }) => (
                    <NumberInput id="ac_hours" {...field} />
                  )} />
                </div>
                <div>
                  <FieldLabel hint="kg/month">LPG / gas</FieldLabel>
                  <Controller name="lpg_usage" control={control} render={({ field }) => (
                    <NumberInput id="lpg_usage" {...field} />
                  )} />
                </div>
              </div>
              <Controller name="solar_usage" control={control} render={({ field }) => (
                <Toggle checked={field.value} onChange={field.onChange} label="Solar panels installed" />
              )} />
            </div>
          )}

          {/* STEP 3 */}
          {step === 3 && (
            <div className="space-y-5 animate-fade-in">
              <h2 className="text-xl font-bold text-slate-100">Food & Diet</h2>
              <div>
                <FieldLabel>Diet type</FieldLabel>
                <Controller name="diet_type" control={control} render={({ field }) => (
                  <SelectCard options={[
                    { value: 'vegetarian', label: 'Vegetarian' },
                    { value: 'mixed', label: 'Mixed' },
                    { value: 'non_vegetarian', label: 'Non-Vegetarian' }
                  ]} value={field.value} onChange={field.onChange} />
                )} />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <FieldLabel hint="people">Household size</FieldLabel>
                  <Controller name="household_size" control={control} render={({ field }) => (
                    <NumberInput id="household_size" {...field} min={1} />
                  )} />
                </div>
                <div>
                  <FieldLabel hint="% (Optional)">Food waste</FieldLabel>
                  <Controller name="food_waste_percentage" control={control} render={({ field }) => (
                    <NumberInput id="food_waste_percentage" {...field} max={100} />
                  )} />
                </div>
              </div>
            </div>
          )}

          {/* STEP 4 */}
          {step === 4 && (
            <div className="space-y-5 animate-fade-in">
              <h2 className="text-xl font-bold text-slate-100">Water Consumption</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <FieldLabel hint="liters/day">Daily water usage</FieldLabel>
                  <Controller name="daily_water_liters" control={control} render={({ field }) => (
                    <NumberInput id="daily_water_liters" {...field} />
                  )} />
                </div>
                <div>
                  <FieldLabel hint="minutes">Avg shower duration</FieldLabel>
                  <Controller name="shower_duration_minutes" control={control} render={({ field }) => (
                    <NumberInput id="shower_duration_minutes" {...field} />
                  )} />
                </div>
              </div>
            </div>
          )}

          {/* STEP 5 */}
          {step === 5 && (
            <div className="space-y-5 animate-fade-in">
              <h2 className="text-xl font-bold text-slate-100">Waste Generation</h2>
              <div>
                <FieldLabel hint="1=Never, 5=Always">Recycling Score</FieldLabel>
                <Controller name="recycling_score" control={control} render={({ field }) => (
                  <NumberInput id="recycling_score" {...field} min={1} max={5} />
                )} />
              </div>
              <div>
                <FieldLabel hint="1=Minimal, 5=Heavy">Plastic Usage Score</FieldLabel>
                <Controller name="plastic_usage_score" control={control} render={({ field }) => (
                  <NumberInput id="plastic_usage_score" {...field} min={1} max={5} />
                )} />
              </div>
            </div>
          )}

          {/* STEP 6 */}
          {step === 6 && (
            <div className="space-y-5 animate-fade-in">
              <h2 className="text-xl font-bold text-slate-100">Housing Characteristics</h2>
              <div>
                <FieldLabel hint="sq meters">House size</FieldLabel>
                <Controller name="house_size_sqm" control={control} render={({ field }) => (
                  <NumberInput id="house_size_sqm" {...field} />
                )} />
              </div>
            </div>
          )}

          {/* STEP 7 */}
          {step === 7 && (
            <div className="space-y-5 animate-fade-in">
              <h2 className="text-xl font-bold text-slate-100">Digital Footprint</h2>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <FieldLabel hint="hrs/day">Screen time</FieldLabel>
                  <Controller name="screen_time_hours" control={control} render={({ field }) => (
                    <NumberInput id="screen_time_hours" {...field} />
                  )} />
                </div>
                <div>
                  <FieldLabel hint="hrs/day">Streaming</FieldLabel>
                  <Controller name="streaming_hours" control={control} render={({ field }) => (
                    <NumberInput id="streaming_hours" {...field} />
                  )} />
                </div>
                <div>
                  <FieldLabel hint="hrs/day">Gaming</FieldLabel>
                  <Controller name="gaming_hours" control={control} render={({ field }) => (
                    <NumberInput id="gaming_hours" {...field} />
                  )} />
                </div>
              </div>
            </div>
          )}

          {/* STEP 8 */}
          {step === 8 && (
            <div className="space-y-5 animate-fade-in">
              <h2 className="text-xl font-bold text-slate-100">Shopping Behavior</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <FieldLabel hint="items/month">New clothes</FieldLabel>
                  <Controller name="new_clothes_monthly" control={control} render={({ field }) => (
                    <NumberInput id="new_clothes_monthly" {...field} />
                  )} />
                </div>
                <div>
                  <FieldLabel hint="items/year">Electronics</FieldLabel>
                  <Controller name="electronics_purchases_yearly" control={control} render={({ field }) => (
                    <NumberInput id="electronics_purchases_yearly" {...field} />
                  )} />
                </div>
              </div>
            </div>
          )}

          {/* STEP 9 */}
          {step === 9 && (
            <div className="space-y-5 animate-fade-in">
              <h2 className="text-xl font-bold text-slate-100">Occupation / Lifestyle</h2>
              <p className="text-sm text-muted">Your profile says you are: <span className="font-medium text-emerald-400 capitalize">{user?.lifestyle_type?.replace('_', ' ') || 'Unknown'}</span></p>
              
              {user?.lifestyle_type === 'professional' || user?.lifestyle_type === 'business_owner' ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <FieldLabel hint="days/week">Commute days</FieldLabel>
                    <Controller name="commute_days_per_week" control={control} render={({ field }) => (
                      <NumberInput id="commute_days_per_week" {...field} max={7} />
                    )} />
                  </div>
                  <div>
                    <FieldLabel hint="%">Remote work</FieldLabel>
                    <Controller name="remote_work_percentage" control={control} render={({ field }) => (
                      <NumberInput id="remote_work_percentage" {...field} max={100} />
                    )} />
                  </div>
                </div>
              ) : (
                <p className="text-sm text-slate-300">No specific questions for your role. Proceed to next step.</p>
              )}
            </div>
          )}

          {/* STEP 10 */}
          {step === 10 && (
            <div className="space-y-5 animate-fade-in">
              <h2 className="text-xl font-bold text-slate-100">Geographic Location</h2>
              <p className="text-sm text-muted">Helps calculate local grid energy intensity.</p>
              <div>
                <FieldLabel>Country</FieldLabel>
                <Controller name="assessment_country" control={control} render={({ field }) => (
                  <select
                    {...field}
                    aria-label="Country"
                    className="w-full px-4 py-2.5 rounded-xl bg-deep-ocean/60 border border-slate-700 text-slate-100"
                  >
                    <option value="">Select country...</option>
                    {COUNTRIES.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                )} />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <FieldLabel>State / Province</FieldLabel>
                  <Controller name="assessment_state" control={control} render={({ field }) => (
                    <TextInput id="assessment_state" aria-label="State or Province" {...field} />
                  )} />
                </div>
                <div>
                  <FieldLabel>City</FieldLabel>
                  <Controller name="assessment_city" control={control} render={({ field }) => (
                    <TextInput id="assessment_city" aria-label="City" {...field} />
                  )} />
                </div>
              </div>
            </div>
          )}

          {/* STEP 11 */}
          {step === 11 && (
            <div className="space-y-5 animate-fade-in">
              <h2 className="text-xl font-bold text-slate-100">Sustainability Practices</h2>
              <p className="text-sm text-muted">Tell us about your green actions to apply carbon offsets.</p>
              <Controller name="composting_active" control={control} render={({ field }) => (
                <Toggle checked={field.value || false} onChange={field.onChange} label="Active Composting" />
              )} />
              <Controller name="green_transport_choices" control={control} render={({ field }) => (
                <Toggle checked={field.value || false} onChange={field.onChange} label="Always prefer green transport" />
              )} />
              <div>
                <FieldLabel hint="number of trees">Trees planted this month</FieldLabel>
                <Controller name="tree_planting_count" control={control} render={({ field }) => (
                  <NumberInput id="tree_planting_count" {...field} />
                )} />
              </div>
            </div>
          )}

          {/* STEP 12 */}
          {step === 12 && (
            <div className="space-y-5 animate-fade-in">
              <h2 className="text-xl font-bold text-slate-100">Review & Submit</h2>
              <p className="text-sm text-muted mb-4">You have completed all sections. Ready to view your footprint?</p>
              
              {apiError && (
                <div className="p-3 bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg text-sm">
                  {apiError}
                </div>
              )}
            </div>
          )}

          {/* Navigation Buttons */}
          <div className={`flex gap-3 mt-8 ${step === 1 ? 'justify-end' : 'justify-between'}`}>
            {step > 1 && (
              <button type="button" onClick={goBack} disabled={isSubmitting} className="px-5 py-2.5 rounded-xl border border-slate-700 text-slate-300 hover:bg-slate-800 transition-colors">
                Back
              </button>
            )}
            {step < STEPS.length ? (
              <button type="button" onClick={goNext} className="px-6 py-2.5 rounded-xl bg-earth-green text-white font-semibold hover:bg-emerald-500 transition-colors">
                Next
              </button>
            ) : (
              <button type="button" onClick={onSubmit} disabled={isSubmitting} className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-emerald-600 text-white font-bold hover:shadow-lg hover:shadow-emerald-500/30 transition-all">
                {isSubmitting ? 'Calculating...' : 'Submit Assessment'}
              </button>
            )}
          </div>

        </div>
      </div>
    </div>
  )
}
