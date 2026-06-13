/**
 * simulator.ts — Carbon Horizon simulator API client
 *
 * Endpoints
 * ---------
 * POST /api/v1/simulator/run     → SimulationResult  (not persisted)
 * POST /api/v1/simulator/save    → SimulationSaved   (persists)
 * GET  /api/v1/simulator/history → SimulationSaved[]
 *
 * Bearer token injected automatically by AuthContext interceptor.
 */
import apiClient from './client'
import type { AssessmentResult } from './assessment'

// ─── Change types (mirror backend ScenarioChanges) ───────────────────────────

export type TransportMode = 'car' | 'motorcycle' | 'bus' | 'train' | 'flight' | 'bicycle'
export type DietType      = 'vegetarian' | 'mixed' | 'non_vegetarian'

export interface TransportChanges {
  new_mode?:        TransportMode
  new_distance_km?: number
}

export interface EnergyChanges {
  electricity_reduction_pct?: number   // 0-100
  reduced_ac?:                boolean
  solar_adoption?:            boolean
}

export interface FoodChanges {
  new_diet_type?: DietType
}

export interface WasteChanges {
  recycling_improvement?: number   // 0-5
  plastic_reduction?:     number   // 0-5
}

export interface ScenarioChanges {
  transport?: TransportChanges
  energy?:    EnergyChanges
  food?:      FoodChanges
  waste?:     WasteChanges
}

// ─── Request bodies ───────────────────────────────────────────────────────────

/** POST /simulator/run */
export interface SimulationRunRequest {
  scenario_name:         string
  scenario_description?: string
  changes:               ScenarioChanges

  // Baseline inputs (from latest assessment)
  transport_mode?:      TransportMode
  distance_km?:         number
  electricity_kwh?:     number
  ac_hours?:            number
  lpg_usage?:           number
  solar_usage?:         boolean
  diet_type?:           DietType
  recycling_score?:     number
  plastic_usage_score?: number
  household_size?:      number
}

/** POST /simulator/save */
export interface SimulationSaveRequest {
  scenario_name:         string
  scenario_description?: string
  current_emission:      number
  projected_emission:    number
  carbon_saved:          number
  reduction_percentage:  number
  simulation_data?:      SimulationData
}

// ─── Response types ───────────────────────────────────────────────────────────

export interface CategoryBreakdown {
  transport: number
  energy:    number
  food:      number
  waste:     number
  total:     number
  score:     number
}

export interface SimulationData {
  current:           CategoryBreakdown
  projected:         CategoryBreakdown
  changes_applied:   Record<string, string>
  factor_version:    string
  calculation_version: string
}

export interface SimulationResult {
  scenario_name:        string
  current_emission:     number
  projected_emission:   number
  carbon_saved:         number
  reduction_percentage: number
  simulation_data:      SimulationData
}

export interface SimulationSaved {
  id:                     string
  scenario_name:          string
  scenario_description:   string | null
  current_emission:       number | null
  projected_emission:     number | null
  reduction_percentage:   number | null
  estimated_carbon_saved: number | null
  simulation_data:        SimulationData | null
  created_at:             string
}

// ─── API envelope ──────────────────────────────────────────────────────────────

interface ApiEnvelope<T> {
  success: boolean
  data?:   T
  error?:  { code: string; message: string }
}

function unwrap<T>(envelope: ApiEnvelope<T>): T {
  if (!envelope.success || !envelope.data) {
    throw new Error(envelope.error?.message ?? 'An unexpected error occurred')
  }
  return envelope.data
}

// ─── API calls ────────────────────────────────────────────────────────────────

export const simulatorApi = {
  /** POST /api/v1/simulator/run → SimulationResult (not saved) */
  run: async (payload: SimulationRunRequest): Promise<SimulationResult> => {
    const res = await apiClient.post<ApiEnvelope<SimulationResult>>('/simulator/run', payload)
    return unwrap(res.data)
  },

  /** POST /api/v1/simulator/save → SimulationSaved */
  save: async (payload: SimulationSaveRequest): Promise<SimulationSaved> => {
    const res = await apiClient.post<ApiEnvelope<SimulationSaved>>('/simulator/save', payload)
    return unwrap(res.data)
  },

  /** GET /api/v1/simulator/history → SimulationSaved[] */
  history: async (): Promise<SimulationSaved[]> => {
    const res = await apiClient.get<ApiEnvelope<SimulationSaved[]>>('/simulator/history')
    return unwrap(res.data)
  },
}

export default simulatorApi
