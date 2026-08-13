import api from './api';
import type { DashboardSummary, SalesAnalytics, CustomerAnalytics, InventoryAnalytics } from '../types';

export const analyticsApi = {
  getDashboard: () =>
    api.get<DashboardSummary>('/analytics/dashboard').then((r) => r.data),

  getSales: () =>
    api.get<SalesAnalytics>('/analytics/sales').then((r) => r.data),

  getCustomers: () =>
    api.get<CustomerAnalytics>('/analytics/customers').then((r) => r.data),

  getInventory: () =>
    api.get<InventoryAnalytics>('/analytics/inventory').then((r) => r.data),
};
export const analyticsService = analyticsApi;
