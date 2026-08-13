import api from './api';
import type { PaginatedResponse, Product, ProductCreate, ProductUpdate } from '../types';

export interface ProductParams {
  skip?: number;
  limit?: number;
  category?: string;
  brand?: string;
  status?: string;
}

export const productApi = {
  getAll: (params: ProductParams = {}) =>
    api.get<PaginatedResponse<Product>>('/products', { params }).then((r) => r.data),

  getById: (id: string) =>
    api.get<Product>(`/products/${id}`).then((r) => r.data),

  create: (data: ProductCreate) =>
    api.post<Product>('/products', data).then((r) => r.data),

  update: (id: string, data: ProductUpdate) =>
    api.put<Product>(`/products/${id}`, data).then((r) => r.data),

  delete: (id: string) =>
    api.delete(`/products/${id}`),
};
export const productService = productApi;
