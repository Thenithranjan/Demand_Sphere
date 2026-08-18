import api from './api';
import type { PaginatedResponse, Sale, SaleCreate } from '../types';

export interface SaleParams {
  skip?: number;
  limit?: number;
  customer_id?: string;
  product_id?: string;
  festival?: string;
  season?: string;
}

export const salesApi = {
  getAll: (params: SaleParams = {}) =>
    api.get<PaginatedResponse<Sale>>('/sales', { params }).then((r) => r.data),

  getById: (id: string) =>
    api.get<Sale>(`/sales/${id}`).then((r) => r.data),

  create: (data: SaleCreate) =>
    api.post<Sale>('/sales', data).then((r) => r.data),

  delete: (id: string) =>
    api.delete(`/sales/${id}`),
};
export const salesService = salesApi;
