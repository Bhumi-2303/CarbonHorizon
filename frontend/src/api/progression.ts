import client from './client';

export interface Badge {
  id: string;
  name: string;
  description: string;
  unlocked: boolean;
  icon: string;
}

export interface ProgressionStats {
  assessments_count: number;
  goals_completed: number;
  habits_logged: number;
  emission_reduction_tons: number;
}

export interface ProgressionData {
  level: string;
  points: number;
  next_level_points: number;
  progress_percentage: number;
  stats: ProgressionStats;
  badges: Badge[];
}

export interface ProgressionResponse {
  success: boolean;
  data: ProgressionData;
}

export const progressionApi = {
  getProgression: async (): Promise<ProgressionResponse> => {
    const response = await client.get<ProgressionResponse>('/progression');
    return response.data;
  },
};
