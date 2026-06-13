import apiClient from './client'

export interface Goal {
  id: string
  user_id: string
  goal_name: string
  goal_description?: string
  target_reduction_percentage?: number
  target_emission_value?: number
  current_progress: number
  target_date?: string
  status: 'active' | 'completed' | 'expired'
}

export interface GoalCreate {
  goal_name: string
  goal_description?: string
  target_reduction_percentage?: number
  target_emission_value?: number
  target_date?: string
}

export interface GoalUpdate {
  goal_name?: string
  goal_description?: string
  target_reduction_percentage?: number
  target_emission_value?: number
  target_date?: string
}

export const goalsApi = {
  list: async (): Promise<Goal[]> => {
    const res = await apiClient.get<{ success: boolean; data: Goal[] }>('/goals/')
    return res.data.data
  },

  listActive: async (): Promise<Goal[]> => {
    const res = await apiClient.get<{ success: boolean; data: Goal[] }>('/goals/active')
    return res.data.data
  },

  get: async (id: string): Promise<Goal> => {
    const res = await apiClient.get<{ success: boolean; data: Goal }>(`/goals/${id}`)
    return res.data.data
  },

  create: async (data: GoalCreate): Promise<Goal> => {
    const res = await apiClient.post<{ success: boolean; data: Goal }>('/goals/', data)
    return res.data.data
  },

  update: async (id: string, data: GoalUpdate): Promise<Goal> => {
    const res = await apiClient.patch<{ success: boolean; data: Goal }>(`/goals/${id}`, data)
    return res.data.data
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/goals/${id}`)
  }
}
