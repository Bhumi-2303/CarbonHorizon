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
  household_size?: number
  assessment_period?: 'daily' | 'monthly' | 'annual'

  // Extensions
  vehicle_type?: string
  fuel_type?: string
  trips_per_week?: number
  public_transport_usage?: string
  carpooling_frequency?: string
  air_travel_frequency?: string
  train_travel_frequency?: string
  walking_cycling_hours?: number

  energy_efficiency_rating?: string
  heating_type?: string

  local_food_frequency?: string
  food_waste_percentage?: number

  daily_water_liters?: number
  shower_duration_minutes?: number
  water_heating_type?: string

  composting_frequency?: string
  ewaste_disposal_method?: string

  house_size_sqm?: number
  home_insulation_level?: string

  screen_time_hours?: number
  streaming_hours?: number
  gaming_hours?: number

  new_clothes_monthly?: number
  second_hand_purchases?: string
  electronics_purchases_yearly?: number

  commute_days_per_week?: number
  remote_work_percentage?: number

  assessment_country?: string
  assessment_state?: string
  assessment_city?: string

  composting_active?: boolean
  tree_planting_count?: number
  reusable_products_usage?: string
  green_transport_choices?: boolean
}

export interface AssessmentResult {
  assessment_id: string
  total_emission: number
  transport: number
  energy: number
  food: number
  waste: number
  housing?: number
  water?: number
  digital?: number
  shopping?: number
  offsets?: number
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
