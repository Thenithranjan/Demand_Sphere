import api from './api';
import type { RecommendationResponse } from '../types';

export const recommendationApi = {
  getForCustomer: (customerId: string, topN: number = 10) =>
    api
      .get<RecommendationResponse>(`/recommendations/${customerId}`, {
        params: { top_n: topN },
      })
      .then((r) => r.data),
};
export const recommendationService = recommendationApi;
