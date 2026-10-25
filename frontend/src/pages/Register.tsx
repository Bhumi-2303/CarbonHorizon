/**
 * Register.tsx — Carbon Horizon account creation page
 *
 * Validation: Zod schema (client-side)
 * Form state: React Hook Form
 * Submission: POST /api/v1/auth/register → login → store tokens in AuthContext
 * On success: redirect to /dashboard
 */
import { useState, useMemo, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Link, useNavigate } from 'react-router-dom'
import { AuthLayout } from '@/components/ui/AuthLayout'
import { FormField } from '@/components/ui/FormField'
import { useAuth } from '@/context/AuthContext'
import { authApi } from '@/api/auth'
import { OCCUPATIONS, isOccupationValidForAge, getOccupationLockReason } from '@/config/occupations'
import Seo from '@/components/Seo'
import { SEO_PAGES } from '@/config/seo'
import { track } from '@/analytics'
import { useConsent } from '@/context/ConsentContext'
import {
  loadGeoDataOnDemand,
  preloadGeoDataIdle,
  type GeoDataModule,
} from '@/services/geoService'

// ─── Zod schema ──────────────────────────────────────────────────────────────

const registerSchema = z.object({
  full_name: z
    .string()
    .min(1, 'Full name is required')
    .max(100, 'Full name is too long'),
  email: z.string().min(1, 'Email is required').email('Enter a valid email'),
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .max(128, 'Password is too long')
    .refine((v) => !/^\d+$/.test(v), {
      message: 'Password must not be all digits',
    })
    .refine((v) => /[A-Z]/.test(v), {
      message: 'Password must contain at least one uppercase letter',
    })
    .refine((v) => /[a-z]/.test(v), {
      message: 'Password must contain at least one lowercase letter',
    })
    .refine((v) => /[0-9]/.test(v), {
      message: 'Password must contain at least one number',
    }),
  honeypot: z.string().optional(),
  age: z.coerce.number().int().min(1, 'Age is required').max(150, 'Invalid age'),
  gender: z.enum(['Male', 'Female', 'Non-Binary', 'Prefer Not to Say']),
  age_group: z
    .enum(['child', 'student', 'adult', 'senior'])
    .optional()
    .or(z.literal('')),
  lifestyle_type: z
    .enum(['student', 'professional', 'homemaker', 'house_helper', 'retired', 'self_employed', 'business_owner', 'consultant'])
    .optional()
    .or(z.literal('')),
  country: z.string().min(1, 'Country is required'),
  state_province: z.string().min(1, 'State/Province is required'),
  city: z.string().min(1, 'City is required'),
  terms_accepted: z.boolean().refine((val) => val === true, {
    message: 'You must accept the Terms of Service and Privacy Policy',
  }),
})

type RegisterFormData = z.infer<typeof registerSchema>

// ─── Options ─────────────────────────────────────────────────────────────────

const AGE_GROUP_OPTIONS = [
  { value: 'child', label: 'Child (< 18)' },
  { value: 'student', label: 'Student' },
  { value: 'adult', label: 'Adult' },
  { value: 'senior', label: 'Senior (60+)' },
]



const GENDER_OPTIONS = [
  { value: 'Male', label: 'Male' },
  { value: 'Female', label: 'Female' },
  { value: 'Non-Binary', label: 'Non-Binary' },
  { value: 'Prefer Not to Say', label: 'Prefer Not to Say' },
]

function getPasswordStrength(password: string): { score: number; label: string; color: string } {
  if (!password) return { score: 0, label: 'Empty', color: 'bg-white/10' }
  let score = 0
  if (password.length >= 8) score++
  if (/[A-Z]/.test(password)) score++
  if (/[a-z]/.test(password)) score++
  if (/[0-9]/.test(password)) score++
  if (/[^A-Za-z0-9]/.test(password)) score++

  if (score <= 2) return { score: 1, label: 'Weak', color: 'bg-red-500' }
  if (score <= 3) return { score: 2, label: 'Fair', color: 'bg-amber-500' }
  if (score <= 4) return { score: 3, label: 'Good', color: 'bg-blue-500' }
  return { score: 4, label: 'Strong', color: 'bg-emerald-500' }
}

// ─── Spinner icon ─────────────────────────────────────────────────────────────

function Spinner() {
  return (
    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  )
}

function EyeIcon() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
    </svg>
  )
}

function EyeOffIcon() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
    </svg>
  )
}

// ─── Component ───────────────────────────────────────────────────────────────

export default function Register() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const { canTrackAnalytics } = useConsent()
  const [apiError, setApiError] = useState<string | null>(null)
  const [showPassword, setShowPassword] = useState(false)

  const [geoData, setGeoData] = useState<GeoDataModule | null>(null)

  useEffect(() => {
    track('signup_started', { source: 'register_form' }, { canTrackAnalytics })
  }, [canTrackAnalytics])

  // Defer heavy location database loading to idle period
  useEffect(() => {
    return preloadGeoDataIdle((data) => {
      setGeoData(data)
    })
  }, [])

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormData>({
    // @ts-expect-error: zod resolver type mismatch due to coerce
    resolver: zodResolver(registerSchema),
    defaultValues: {
      full_name: '',
      email: '',
      password: '',
      age: '' as unknown as number,
      gender: '' as any,
      age_group: '',
      lifestyle_type: '',
      country: '',
      state_province: '',
      city: '',
      terms_accepted: false,
      honeypot: '',
    },
  })

  // Cascading location logic
  const selectedCountryCode = watch('country')
  const selectedStateCode = watch('state_province')
  const currentAge = watch('age')
  const watchedPassword = watch('password') || ''
  const passwordStrength = useMemo(() => getPasswordStrength(watchedPassword), [watchedPassword])

  const lifestyleOptions = useMemo(() => {
    return OCCUPATIONS.map((occ) => {
      const isValid = isOccupationValidForAge(occ.id, currentAge)
      return {
        value: occ.id,
        label: occ.label,
        disabled: !isValid,
        title: !isValid ? getOccupationLockReason(occ.id) : undefined,
      }
    })
  }, [currentAge])

  const countryOptions = useMemo(() => {
    if (!geoData) return []
    return geoData.Country.getAllCountries().map((c: any) => ({
      value: c.isoCode,
      label: c.name
    }))
  }, [geoData])

  const stateOptions = useMemo(() => {
    if (!selectedCountryCode || !geoData) return []
    return geoData.State.getStatesOfCountry(selectedCountryCode).map((s: any) => ({
      value: s.isoCode,
      label: s.name
    }))
  }, [selectedCountryCode, geoData])

  const cityOptions = useMemo(() => {
    if (!selectedCountryCode || !selectedStateCode || !geoData) return []
    return geoData.City.getCitiesOfState(selectedCountryCode, selectedStateCode).map((c: any) => ({
      value: c.name, // City usually doesn't have an ISO code, we store name
      label: c.name
    }))
  }, [selectedCountryCode, selectedStateCode, geoData])

  const onSubmit = async (data: RegisterFormData) => {
    setApiError(null)
    try {
      // Resolve names for backend instead of ISO codes
      const geo = geoData || await loadGeoDataOnDemand()
      const countryObj = geo ? geo.Country.getCountryByCode(data.country) : null
      const stateObj = geo ? geo.State.getStateByCodeAndCountry(data.state_province, data.country) : null

      const termsTimestamp = new Date().toISOString()
      const termsVersion = '2026-v1'

      try {
        localStorage.setItem(
          'ch_terms_acceptance',
          JSON.stringify({
            accepted: true,
            version: termsVersion,
            timestamp: termsTimestamp,
          })
        )
      } catch (err) {
        console.error('Failed to store terms acceptance', err)
      }

      const payload = {
        full_name: data.full_name,
        email: data.email,
        password: data.password,
        age: data.age,
        gender: data.gender,
        country: countryObj ? countryObj.name : data.country,
        state_province: stateObj ? stateObj.name : data.state_province,
        city: data.city,
        terms_accepted: true,
        terms_version: termsVersion,
        terms_accepted_at: termsTimestamp,
        honeypot: data.honeypot || '',
        turnstile_token: 'test-turnstile-token',
        ...(data.age_group ? { age_group: data.age_group as any } : {}),
        ...(data.lifestyle_type ? { lifestyle_type: data.lifestyle_type as any } : {}),
      }

      const result = await authApi.register(payload as any)
      // Auto-login after registration
      const tokens = await authApi.login({ email: data.email, password: data.password })
      login(tokens, result.user)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setApiError(err instanceof Error ? err.message : 'Registration failed. Please try again.')
    }
  }

  const btnCls =
    'w-full py-2.5 px-4 rounded-xl font-semibold text-sm text-primary ' +
    'bg-gradient-to-r from-emerald-500 to-emerald-600 ' +
    'hover:from-emerald-400 hover:to-emerald-500 ' +
    'disabled:opacity-60 disabled:cursor-not-allowed ' +
    'shadow-lg shadow-emerald-500/25 hover:shadow-emerald-500/40 ' +
    'transition-all duration-200 flex items-center justify-center gap-2'

  return (
    <AuthLayout title="Create your account" subtitle="Start tracking your carbon footprint today">
      <Seo {...SEO_PAGES.signup} />
      {/* @ts-expect-error: handleSubmit type mismatch */}
      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">

        {/* API error banner */}
        {apiError && (
          <div role="alert" aria-live="assertive" className="flex items-start gap-2.5 p-3.5 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
            <svg className="w-4 h-4 mt-0.5 shrink-0" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <span>{apiError}</span>
          </div>
        )}

        {/* Full name */}
        <FormField
          as="input"
          fieldId="full_name"
          label="Full name"
          type="text"
          placeholder="Priya Sharma"
          required
          autoComplete="name"
          error={errors.full_name?.message as string}
          {...register('full_name')}
        />

        {/* Email */}
        <FormField
          as="input"
          fieldId="email"
          label="Email address"
          type="email"
          placeholder="priya@example.com"
          required
          autoComplete="email"
          error={errors.email?.message as string}
          {...register('email')}
        />

        {/* Password with show/hide */}
        <div className="relative">
          <FormField
            as="input"
            fieldId="password"
            label="Password"
            type={showPassword ? 'text' : 'password'}
            placeholder="Min. 8 characters"
            required
            autoComplete="new-password"
            error={errors.password?.message as string}
            {...register('password')}
          />
          <button
            type="button"
            onClick={() => setShowPassword((v) => !v)}
            className="absolute right-3 top-[34px] text-muted hover:text-muted transition-colors"
            aria-label={showPassword ? 'Hide password' : 'Show password'}
          >
            {showPassword ? <EyeOffIcon /> : <EyeIcon />}
          </button>
        </div>

        {/* Password Strength Meter */}
        {watchedPassword.length > 0 && (
          <div className="space-y-1.5" aria-live="polite">
            <div className="flex justify-between text-xs text-muted">
              <span>Password strength</span>
              <span className="font-medium text-primary">{passwordStrength.label}</span>
            </div>
            <div className="h-1.5 w-full bg-white/10 rounded-full overflow-hidden flex gap-1">
              {[1, 2, 3, 4].map((step) => (
                <div
                  key={step}
                  className={`h-full flex-1 transition-all duration-300 ${
                    step <= passwordStrength.score ? passwordStrength.color : 'bg-white/10'
                  }`}
                />
              ))}
            </div>
          </div>
        )}

        {/* Hidden Honeypot for bot protection */}
        <input
          type="text"
          id="honeypot"
          autoComplete="off"
          tabIndex={-1}
          aria-hidden="true"
          className="hidden opacity-0 absolute -z-10 w-0 h-0 pointer-events-none"
          {...register('honeypot')}
        />

        {/* Age + Gender */}
        <div className="grid grid-cols-2 gap-3">
          <FormField
            as="input"
            fieldId="age"
            label="Age"
            type="number"
            placeholder="Age"
            required
            error={errors.age?.message as string}
            {...register('age')}
          />
          <FormField
            as="select"
            fieldId="gender"
            label="Gender"
            placeholder="Select…"
            required
            options={GENDER_OPTIONS}
            error={errors.gender?.message as string}
            {...register('gender')}
          />
        </div>

        {/* Age group + Lifestyle */}
        <div className="grid grid-cols-2 gap-3">
          <FormField
            as="select"
            fieldId="age_group"
            label="Age group"
            placeholder="Select…"
            options={AGE_GROUP_OPTIONS}
            error={errors.age_group?.message as string}
            {...register('age_group')}
          />
          <FormField
            as="select"
            fieldId="lifestyle_type"
            label="Lifestyle / Occupation"
            placeholder="Select…"
            options={lifestyleOptions}
            error={errors.lifestyle_type?.message as string}
            {...register('lifestyle_type')}
          />
        </div>

        {/* Cascading Location: Country -> State -> City */}
        <FormField
          as="select"
          fieldId="country"
          label="Country"
          placeholder={countryOptions.length === 0 ? "Select Country (click to load)…" : "Select Country…"}
          required
          options={countryOptions}
          error={errors.country?.message as string}
          onFocus={() => loadGeoDataOnDemand().then(setGeoData)}
          onPointerDown={() => loadGeoDataOnDemand().then(setGeoData)}
          {...register('country', {
            onChange: () => {
              setValue('state_province', '')
              setValue('city', '')
            }
          })}
        />

        <div className="grid grid-cols-2 gap-3">
          <FormField
            as="select"
            fieldId="state_province"
            label="State / Province"
            placeholder="Select State…"
            required
            disabled={!selectedCountryCode}
            options={stateOptions}
            error={errors.state_province?.message as string}
            {...register('state_province', {
              onChange: () => {
                setValue('city', '')
              }
            })}
          />
          <FormField
            as="select"
            fieldId="city"
            label="City"
            placeholder="Select City…"
            required
            disabled={!selectedStateCode}
            options={cityOptions}
            error={errors.city?.message as string}
            {...register('city')}
          />
        </div>

        {/* Terms & Privacy Acceptance */}
        <div className="pt-1">
          <label className="flex items-start gap-2.5 cursor-pointer text-xs text-slate-300">
            <input
              type="checkbox"
              {...register('terms_accepted')}
              className="mt-0.5 w-4 h-4 rounded border-white/20 bg-white/5 text-earth-green focus:ring-earth-green shrink-0 cursor-pointer"
            />
            <span>
              I agree to the{' '}
              <Link to="/terms" target="_blank" rel="noopener noreferrer" className="text-earth-green underline hover:text-emerald-300 font-medium">
                Terms of Service
              </Link>{' '}
              and{' '}
              <Link to="/privacy" target="_blank" rel="noopener noreferrer" className="text-earth-green underline hover:text-emerald-300 font-medium">
                Privacy Policy
              </Link>
              . I confirm that users under 13 have parental or guardian consent.
            </span>
          </label>
          {errors.terms_accepted && (
            <p className="mt-1 text-xs text-red-400">
              {errors.terms_accepted.message as string}
            </p>
          )}
        </div>

        {/* Submit */}
        <button type="submit" disabled={isSubmitting} className={btnCls}>
          {isSubmitting ? <><Spinner /> Creating account…</> : 'Create account'}
        </button>

        {/* Login link */}
        <p className="text-center text-sm text-muted pt-1">
          Already have an account?{' '}
          <Link to="/login" className="text-earth-green hover:text-emerald-300 font-medium transition-colors">
            Sign in
          </Link>
        </p>
      </form>
    </AuthLayout>
  )
}
