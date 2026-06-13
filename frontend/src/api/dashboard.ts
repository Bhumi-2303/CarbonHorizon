import apiClient from './client'

export interface DashboardAssessment {
  total_emission: number
  transport_emission: number
  energy_emission: number
  food_emission: number
  waste_emission: number
  carbon_score: number
}

export interface DashboardData {
  latest_assessment: DashboardAssessment | null
  trend_delta: number
  active_goals_count: number
  current_habit_streak: number
  forecast_summary: {
    month_3_emission: number
  } | null
}

export const dashboardApi = {
  getDashboard: async (): Promise<DashboardData> => {
    // According to the prompt, GET /api/dashboard returns this shape.
    // The actual route in the backend might be under /v1 or /dashboard. We'll use /dashboard
    // If the backend wraps it in a { success: true, data: ... } we unwrap it, otherwise we return it.
    const res = await apiClient.get<any>('/dashboard')
    // Handle both wrapped and unwrapped just in case
    return res.data.data ? res.data.data : res.data
  }
}
