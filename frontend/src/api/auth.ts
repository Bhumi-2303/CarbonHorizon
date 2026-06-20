/**
 * auth.ts — Carbon Horizon auth API client
 *
 * Talks to the FastAPI backend at /api/v1/auth/*
 * All responses are unwrapped from the APIResponse envelope:
 *   { success: true, data: { ... } }
 */
import apiClient from './client'

// ─── Types ──────────────────────────────────────────────────────────────────

export type AgeGroup = 'child' | 'student' | 'adult' | 'senior'
export type LifestyleType = 'student' | 'professional' | 'homemaker' | 'house_helper' | 'retired' | 'self_employed' | 'business_owner' | 'consultant'
export type Gender = 'Male' | 'Female' | 'Non-Binary' | 'Prefer Not to Say'

export interface RegisterPayload {
  full_name: string
  email: string
  password: string
  age: number
  gender: Gender
  age_group?: AgeGroup
  lifestyle_type?: LifestyleType
  country: string
  state_province: string
  city: string
}

export interface LoginPayload {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface UserProfile {
  id: string
  full_name: string
  email: string
  age: number | null
  gender: Gender | null
  age_group: AgeGroup | null
  lifestyle_type: LifestyleType | null
  country: string | null
  state_province: string | null
  city: string | null
  email_verified: boolean
  last_login: string | null
  created_at: string
  updated_at: string
}

export interface RegisterResponse {
  user: UserProfile
  message: string
}

/** Backend APIResponse envelope */
interface ApiEnvelope<T> {
  success: boolean
  data?: T
  error?: { code: string; message: string }
}

// ─── Helpers ────────────────────────────────────────────────────────────────

/** Unwrap the APIResponse envelope; throw a friendly error on failure. */
function unwrap<T>(envelope: ApiEnvelope<T>): T {
  if (!envelope.success || !envelope.data) {
    const msg = envelope.error?.message ?? 'An unexpected error occurred'
    throw new Error(msg)
  }
  return envelope.data
}

// ─── API calls ──────────────────────────────────────────────────────────────

export const authApi = {
  /** POST /api/v1/auth/register → { user, message } */
  register: async (payload: RegisterPayload): Promise<RegisterResponse> => {
    const res = await apiClient.post<ApiEnvelope<RegisterResponse>>(
      '/auth/register',
      payload,
    )
    return unwrap(res.data)
  },

  /** POST /api/v1/auth/login → TokenResponse */
  login: async (payload: LoginPayload): Promise<TokenResponse> => {
    const res = await apiClient.post<ApiEnvelope<TokenResponse>>(
      '/auth/login',
      payload,
    )
    return unwrap(res.data)
  },

  /** POST /api/v1/auth/refresh → TokenResponse */
  refresh: async (refreshToken: string): Promise<TokenResponse> => {
    const res = await apiClient.post<ApiEnvelope<TokenResponse>>(
      '/auth/refresh',
      { refresh_token: refreshToken },
    )
    return unwrap(res.data)
  },

  /** POST /api/v1/auth/logout  (204 No Content) */
  logout: async (): Promise<void> => {
    await apiClient.post('/auth/logout')
  },

  /** GET /api/v1/auth/profile → UserProfile */
  getProfile: async (token?: string): Promise<UserProfile> => {
    const config = token ? { headers: { Authorization: `Bearer ${token}` } } : undefined
    const res = await apiClient.get<ApiEnvelope<UserProfile>>('/auth/profile', config)
    return unwrap(res.data)
  },

  /** PUT /api/v1/auth/profile → UserProfile */
  updateProfile: async (payload: Partial<UserProfile>): Promise<UserProfile> => {
    const res = await apiClient.put<ApiEnvelope<UserProfile>>('/auth/profile', payload)
    return unwrap(res.data)
  },

  /** DELETE /api/v1/auth/account */
  deleteAccount: async (): Promise<void> => {
    await apiClient.delete('/auth/account')
  },
}

export default authApi
