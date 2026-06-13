/**
 * assessment.ts — Carbon Horizon assessment API client
 *
 * Talks to the FastAPI backend at /api/v1/assessment/*
 * The axios interceptor in AuthContext injects the Bearer token automatically.
 */
import apiClient from './client'

// ─── Types ──────────────────────────────────────────────────────────────────

export type TransportMode =
  | 'car'
  | 'motorcycle'
  | 'bus'
  | 'train'
  | 'flight'
  | 'bicycle'

export type DietType = 'vegetarian' | 'mixed' | 'non_vegetarian'

export interface AssessmentPayload {
  // Step 1 — Transport
  transport_mode: TransportMode
  distance_km: number

  // Step 2 — Energy
  electricity_kwh: number
  ac_hours: number
  lpg_usage: number
  solar_usage: boolean

  // Step 3 — Food & Waste
  diet_type: DietType
  recycling_score: number
  plastic_usage_score: number
  household_size: number

  // Period — always monthly from the wizard
  assessment_period?: string
}

export interface AssessmentResult {
  assessment_id: string
  total_emission: number
  transport: number
  energy: number
  food: number
  waste: number
  carbon_score: number
  assessment_period: string
  created_at: string
}

/** Backend APIResponse envelope */
interface ApiEnvelope<T> {
  success: boolean
  data?: T
  error?: { code: string; message: string }
}

// ─── Helpers ────────────────────────────────────────────────────────────────

function unwrap<T>(envelope: ApiEnvelope<T>): T {
  if (!envelope.success || !envelope.data) {
    const msg = envelope.error?.message ?? 'An unexpected error occurred'
    throw new Error(msg)
  }
  return envelope.data
}

// ─── API calls ──────────────────────────────────────────────────────────────

export const assessmentApi = {
  /** POST /api/v1/assessment/create → AssessmentResult */
  create: async (payload: AssessmentPayload): Promise<AssessmentResult> => {
    const res = await apiClient.post<ApiEnvelope<AssessmentResult>>(
      '/assessment/create',
      { ...payload, assessment_period: payload.assessment_period ?? 'monthly' },
    )
    return unwrap(res.data)
  },

  /** GET /api/v1/assessment/history → AssessmentResult[] */
  history: async (): Promise<AssessmentResult[]> => {
    const res = await apiClient.get<ApiEnvelope<AssessmentResult[]>>(
      '/assessment/history',
    )
    return unwrap(res.data)
  },

  /** GET /api/v1/assessment/:id → AssessmentResult */
  getById: async (id: string): Promise<AssessmentResult> => {
    const res = await apiClient.get<ApiEnvelope<AssessmentResult>>(
      `/assessment/${id}`,
    )
    return unwrap(res.data)
  },
}

export default assessmentApi
