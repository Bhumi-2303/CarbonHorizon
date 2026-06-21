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
  total_assessments?: number
  active_goals_count: number
  current_habit_streak: number
  forecast_summary: {
    month_3_emission: number
  } | null
}

export const dashboardApi = {
  getDashboard: async (): Promise<DashboardData> => {
    try {
      const res = await apiClient.get<any>('/dashboard')
      return res.data.data ? res.data.data : res.data
    } catch {
      // Polyfill composition because backend /dashboard is a stub
      const [historyRes, goalsRes] = await Promise.all([
        apiClient.get('/assessment/history').catch(() => ({ data: { data: [] } })),
        apiClient.get('/goals').catch(() => ({ data: { data: [] } }))
      ])
      const history = historyRes.data?.data || []
      const goals = goalsRes.data?.data || []
      
      const sortedHistory = [...history].sort((a: any, b: any) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      const latest = sortedHistory.length > 0 ? sortedHistory[0] : null
      
      return {
        latest_assessment: latest,
        trend_delta: 0,
        total_assessments: history.length,
        active_goals_count: goals.filter((g: any) => g.status === 'in_progress').length,
        current_habit_streak: 0,
        forecast_summary: null
      }
    }
  }
}
