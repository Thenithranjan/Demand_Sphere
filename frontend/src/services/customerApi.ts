import api from './api';
import type { PaginatedResponse, Customer, CustomerCreate, CustomerUpdate } from '../types';

export interface CustomerParams {
  skip?: number;
  limit?: number;
  membership?: string;
  city?: string;
}

export const customerApi = {
  getAll: (params: CustomerParams = {}) =>
    api.get<PaginatedResponse<Customer>>('/customers', { params }).then((r) => r.data),

  getById: (id: string) =>
    api.get<Customer>(`/customers/${id}`).then((r) => r.data),

  create: (data: CustomerCreate) =>
    api.post<Customer>('/customers', data).then((r) => r.data),

  update: (id: string, data: CustomerUpdate) =>
    api.put<Customer>(`/customers/${id}`, data).then((r) => r.data),

  delete: (id: string) =>
    api.delete(`/customers/${id}`),
};
export const customerService = customerApi;
