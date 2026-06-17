/**
 * Register.tsx — Carbon Horizon account creation page
 *
 * Validation: Zod schema (client-side)
 * Form state: React Hook Form
 * Submission: POST /api/v1/auth/register → login → store tokens in AuthContext
 * On success: redirect to /dashboard
 */
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Link, useNavigate } from 'react-router-dom'
import { AuthLayout } from '@/components/ui/AuthLayout'
import { FormField } from '@/components/ui/FormField'
import { useAuth } from '@/context/AuthContext'
import { authApi } from '@/api/auth'

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
    }),
  age_group: z
    .enum(['child', 'student', 'adult', 'senior'])
    .optional()
    .or(z.literal('')),
  lifestyle_type: z
    .enum(['student', 'professional', 'homemaker', 'retired'])
    .optional()
    .or(z.literal('')),
  city: z.string().max(100, 'City is too long').optional(),
  country: z.string().max(100, 'Country is too long').optional(),
})

type RegisterFormData = z.infer<typeof registerSchema>

// ─── Options ─────────────────────────────────────────────────────────────────

const AGE_GROUP_OPTIONS = [
  { value: 'child', label: 'Child (< 18)' },
  { value: 'student', label: 'Student' },
  { value: 'adult', label: 'Adult' },
  { value: 'senior', label: 'Senior (60+)' },
]

const LIFESTYLE_OPTIONS = [
  { value: 'student', label: 'Student' },
  { value: 'professional', label: 'Professional' },
  { value: 'homemaker', label: 'Homemaker' },
  { value: 'retired', label: 'Retired' },
]

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
  const [apiError, setApiError] = useState<string | null>(null)
  const [showPassword, setShowPassword] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      full_name: '',
      email: '',
      password: '',
      age_group: '',
      lifestyle_type: '',
      city: '',
      country: '',
    },
  })

  const onSubmit = async (data: RegisterFormData) => {
    setApiError(null)
    try {
      const payload = {
        full_name: data.full_name,
        email: data.email,
        password: data.password,
        ...(data.age_group ? { age_group: data.age_group as 'child' | 'student' | 'adult' | 'senior' } : {}),
        ...(data.lifestyle_type ? { lifestyle_type: data.lifestyle_type as 'student' | 'professional' | 'homemaker' | 'retired' } : {}),
        ...(data.city ? { city: data.city } : {}),
        ...(data.country ? { country: data.country } : {}),
      }

      const result = await authApi.register(payload)
      // Auto-login after registration
      const tokens = await authApi.login({ email: data.email, password: data.password })
      login(tokens, result.user)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setApiError(err instanceof Error ? err.message : 'Registration failed. Please try again.')
    }
  }

  const btnCls =
    'w-full py-2.5 px-4 rounded-xl font-semibold text-sm text-white ' +
    'bg-gradient-to-r from-emerald-500 to-emerald-600 ' +
    'hover:from-emerald-400 hover:to-emerald-500 ' +
    'disabled:opacity-60 disabled:cursor-not-allowed ' +
    'shadow-lg shadow-emerald-500/25 hover:shadow-emerald-500/40 ' +
    'transition-all duration-200 flex items-center justify-center gap-2'

  return (
    <AuthLayout title="Create your account" subtitle="Start tracking your carbon footprint today">
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
          error={errors.full_name?.message}
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
          error={errors.email?.message}
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
            error={errors.password?.message}
            {...register('password')}
          />
          <button
            type="button"
            onClick={() => setShowPassword((v) => !v)}
            className="absolute right-3 top-[34px] text-slate-500 hover:text-slate-300 transition-colors"
            aria-label={showPassword ? 'Hide password' : 'Show password'}
          >
            {showPassword ? <EyeOffIcon /> : <EyeIcon />}
          </button>
        </div>

        {/* Age group + Lifestyle */}
        <div className="grid grid-cols-2 gap-3">
          <FormField
            as="select"
            fieldId="age_group"
            label="Age group"
            placeholder="Select…"
            options={AGE_GROUP_OPTIONS}
            error={errors.age_group?.message}
            {...register('age_group')}
          />
          <FormField
            as="select"
            fieldId="lifestyle_type"
            label="Lifestyle"
            placeholder="Select…"
            options={LIFESTYLE_OPTIONS}
            error={errors.lifestyle_type?.message}
            {...register('lifestyle_type')}
          />
        </div>

        {/* City + Country */}
        <div className="grid grid-cols-2 gap-3">
          <FormField
            as="input"
            fieldId="city"
            label="City"
            type="text"
            placeholder="Mumbai"
            autoComplete="address-level2"
            error={errors.city?.message}
            {...register('city')}
          />
          <FormField
            as="input"
            fieldId="country"
            label="Country"
            type="text"
            placeholder="India"
            autoComplete="country-name"
            error={errors.country?.message}
            {...register('country')}
          />
        </div>

        {/* Submit */}
        <button type="submit" disabled={isSubmitting} className={btnCls}>
          {isSubmitting ? <><Spinner /> Creating account…</> : 'Create account'}
        </button>

        {/* Login link */}
        <p className="text-center text-sm text-slate-400 pt-1">
          Already have an account?{' '}
          <Link to="/login" className="text-emerald-400 hover:text-emerald-300 font-medium transition-colors">
            Sign in
          </Link>
        </p>
      </form>
    </AuthLayout>
  )
}
