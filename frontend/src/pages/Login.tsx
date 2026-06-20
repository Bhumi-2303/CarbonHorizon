/**
 * Login.tsx — Carbon Horizon sign-in page
 */
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { AuthLayout } from '@/components/ui/AuthLayout'
import { FormField } from '@/components/ui/FormField'
import { useAuth } from '@/context/AuthContext'
import { authApi } from '@/api/auth'

// ─── Zod schema ──────────────────────────────────────────────────────────────

const loginSchema = z.object({
  email: z.string().min(1, 'Email is required').email('Enter a valid email'),
  password: z.string().min(1, 'Password is required'),
})

type LoginFormData = z.infer<typeof loginSchema>

// ─── Icons ───────────────────────────────────────────────────────────────────

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

export default function Login() {
  const navigate  = useNavigate()
  const location  = useLocation()
  const { login } = useAuth()
  const [apiError, setApiError]       = useState<string | null>(null)
  const [showPassword, setShowPassword] = useState(false)

  // Redirect back to the page the user was trying to visit
  const redirectTo = (location.state as { from?: string } | null)?.from ?? '/dashboard'

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  })

  const onSubmit = async (data: LoginFormData) => {
    setApiError(null)
    try {
      const tokens = await authApi.login(data)
      const profile = await authApi.getProfile(tokens.access_token)
      login(tokens, profile)
      navigate(redirectTo, { replace: true })
    } catch (err) {
      setApiError(err instanceof Error ? err.message : 'Login failed. Please try again.')
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
    <AuthLayout title="Welcome back" subtitle="Sign in to your Carbon Horizon account">
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

        {/* Email */}
        <FormField
          as="input"
          fieldId="login-email"
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
            fieldId="login-password"
            label="Password"
            type={showPassword ? 'text' : 'password'}
            placeholder="Your password"
            required
            autoComplete="current-password"
            error={errors.password?.message}
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

        {/* Forgot password stub */}
        <div className="flex justify-end -mt-1">
          <span className="text-xs text-muted select-none">
            Forgot password?{' '}
            <span className="text-earth-green/80">(coming soon)</span>
          </span>
        </div>

        {/* Submit */}
        <button type="submit" disabled={isSubmitting} className={btnCls}>
          {isSubmitting ? <><Spinner /> Signing in…</> : 'Sign in'}
        </button>

        {/* Divider */}
        <div className="relative my-1">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-slate-700/60" />
          </div>
          <div className="relative flex justify-center">
            <span className="px-3 text-xs text-muted bg-bg-secondary">New to Carbon Horizon?</span>
          </div>
        </div>

        {/* Register link */}
        <Link
          to="/register"
          className="w-full py-2.5 px-4 rounded-xl text-sm font-medium text-muted
                     border border-slate-700 hover:border-earth-green/50
                     hover:text-earth-green hover:bg-earth-green/5
                     transition-all duration-200 flex items-center justify-center"
        >
          Create a free account
        </Link>
      </form>
    </AuthLayout>
  )
}
