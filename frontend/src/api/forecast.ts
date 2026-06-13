import apiClient from "./client";

export type ForecastType = "current_path" | "recommended_path" | "custom_path";

export interface CustomReductionRates {
  transport?: number;
  energy?: number;
  food?: number;
  waste?: number;
}

export interface ForecastGenerateRequest {
  forecast_type: ForecastType;
  custom_rates?: CustomReductionRates;
}

export interface ForecastPointResponse {
  id: string;
  month_offset: number;
  predicted_emission: number;
  created_at: string;
}

export interface ForecastResponse {
  id: string;
  forecast_type: string;
  created_at: string;
  updated_at: string;
  forecast_points: ForecastPointResponse[];
}

export interface ForecastListItem {
  id: string;
  forecast_type: string;
  point_count: number;
  created_at: string;
}

// ---------------------------------------------------------------------------
// API Calls
// ---------------------------------------------------------------------------

export const generateForecast = async (req: ForecastGenerateRequest): Promise<ForecastResponse> => {
  const { data } = await apiClient.post<{ success: boolean; data: ForecastResponse }>("/forecast/generate", req);
  return data.data;
};

export const getForecastHistory = async (): Promise<ForecastListItem[]> => {
  const { data } = await apiClient.get<{ success: boolean; data: ForecastListItem[] }>("/forecast/history");
  return data.data;
};

export const getForecastById = async (id: string): Promise<ForecastResponse> => {
  const { data } = await apiClient.get<{ success: boolean; data: ForecastResponse }>(`/forecast/${id}`);
  return data.data;
};

export const deleteForecast = async (id: string): Promise<void> => {
  await apiClient.delete(`/forecast/${id}`);
};
