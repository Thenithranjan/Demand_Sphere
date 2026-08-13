import api from './api';
import type { PaginatedResponse, Inventory, InventoryAlert } from '../types';

export interface InventoryParams {
  skip?: number;
  limit?: number;
  status?: string;
  warehouse?: string;
}

export const inventoryApi = {
  getAll: (params: InventoryParams = {}) =>
    api.get<PaginatedResponse<Inventory>>('/inventory', { params }).then((r) => r.data),

  getById: (id: string) =>
    api.get<Inventory>(`/inventory/${id}`).then((r) => r.data),

  getSummary: () =>
    api.get('/inventory/summary').then((r) => r.data),

  getAlerts: () =>
    api.get<InventoryAlert[]>('/inventory/alerts').then((r) => r.data),

  getLowStock: () =>
    api.get<InventoryAlert[]>('/inventory/low-stock').then((r) => r.data),

  getRecommendations: () =>
    api.get<InventoryAlert[]>('/inventory/recommendations').then((r) => r.data),

  getOverstock: () =>
    api.get<Inventory[]>('/inventory/overstock').then((r) => r.data),
};
export const inventoryService = inventoryApi;
