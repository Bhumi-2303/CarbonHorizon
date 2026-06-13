import apiClient from './client'

export interface Habit {
  id: string
  user_id: string
  habit_type: string
  completed: boolean
  carbon_saved: number | null
  activity_date: string
  notes?: string
}

export interface HabitCreate {
  habit_type: string
  activity_date: string
  notes?: string
}

export interface StreakResponse {
  streak: number
}

export interface SummaryResponse {
  start_date: string
  end_date: string
  completed_habits: number
  total_carbon_saved: number
}

export const habitsApi = {
  list: async (startDate?: string, endDate?: string): Promise<Habit[]> => {
    const params = new URLSearchParams()
    if (startDate) params.append('start_date', startDate)
    if (endDate) params.append('end_date', endDate)
    const url = `/habits/${params.toString() ? '?' + params.toString() : ''}`
    const res = await apiClient.get<{ success: boolean; data: Habit[] }>(url)
    return res.data.data
  },

  log: async (data: HabitCreate): Promise<Habit> => {
    const res = await apiClient.post<{ success: boolean; data: Habit }>('/habits/log', data)
    return res.data.data
  },

  getStreak: async (): Promise<StreakResponse> => {
    const res = await apiClient.get<{ success: boolean; data: StreakResponse }>('/habits/streak')
    return res.data.data
  },

  getWeeklySummary: async (): Promise<SummaryResponse> => {
    const res = await apiClient.get<{ success: boolean; data: SummaryResponse }>('/habits/summary/weekly')
    return res.data.data
  },

  getMonthlySummary: async (): Promise<SummaryResponse> => {
    const res = await apiClient.get<{ success: boolean; data: SummaryResponse }>('/habits/summary/monthly')
    return res.data.data
  }
}
