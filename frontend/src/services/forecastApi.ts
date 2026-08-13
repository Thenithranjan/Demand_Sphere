import api from './api';
import type { PaginatedResponse, ForecastResult, ForecastPrediction } from '../types';

export interface ForecastParams {
  skip?: number;
  limit?: number;
  demand_level?: string;
}

export const forecastApi = {
  getAll: (params: ForecastParams = {}) =>
    api.get<PaginatedResponse<ForecastResult>>('/forecast', { params }).then((r) => r.data),

  getDynamicForecast: (productId: string) =>
    api.get<ForecastPrediction>(`/forecast/${productId}`).then((r) => r.data),

  getByProduct: (productId: string) =>
    api.get<ForecastResult[]>(`/forecast/product/${productId}`).then((r) => r.data),
};
export const forecastService = forecastApi;
