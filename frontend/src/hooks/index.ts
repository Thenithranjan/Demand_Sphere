/**
 * Custom Hooks — Retail AI Frontend
 * ====================================
 * Reusable hooks wrapping TanStack Query for data fetching,
 * plus utility hooks for debouncing and media queries.
 */

import { useQuery } from '@tanstack/react-query';
import { useState, useEffect } from 'react';
import { productApi as productService, type ProductParams } from '../services/productApi';
import { customerApi as customerService, type CustomerParams } from '../services/customerApi';
import { salesApi as salesService, type SaleParams } from '../services/salesApi';
import { inventoryApi as inventoryService } from '../services/inventoryApi';
import { forecastApi as forecastService } from '../services/forecastApi';
import { recommendationApi as recommendationService } from '../services/recommendationApi';
import { analyticsApi as analyticsService } from '../services/analyticsApi';
import { userApi as userService } from '../services/userApi';

// ─── Debounce Hook ───────────────────────────────────────────────────────────
export function useDebounce<T>(value: T, delay: number = 300): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debouncedValue;
}

// ─── Media Query Hook ────────────────────────────────────────────────────────
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() =>
    typeof window !== 'undefined' ? window.matchMedia(query).matches : false
  );
  useEffect(() => {
    const media = window.matchMedia(query);
    const listener = (e: MediaQueryListEvent) => setMatches(e.matches);
    media.addEventListener('change', listener);
    setMatches(media.matches);
    return () => media.removeEventListener('change', listener);
  }, [query]);
  return matches;
}

// ─── Products ────────────────────────────────────────────────────────────────
export function useProducts(params: ProductParams = {}) {
  return useQuery({
    queryKey: ['products', params],
    queryFn: () => productService.getAll(params),
  });
}

export function useProduct(id: string) {
  return useQuery({
    queryKey: ['product', id],
    queryFn: () => productService.getById(id),
    enabled: !!id,
  });
}

// ─── Customers ───────────────────────────────────────────────────────────────
export function useCustomers(params: CustomerParams = {}) {
  return useQuery({
    queryKey: ['customers', params],
    queryFn: () => customerService.getAll(params),
  });
}

export function useCustomer(id: string) {
  return useQuery({
    queryKey: ['customer', id],
    queryFn: () => customerService.getById(id),
    enabled: !!id,
  });
}

// ─── Sales ───────────────────────────────────────────────────────────────────
export function useSales(params: SaleParams = {}) {
  return useQuery({
    queryKey: ['sales', params],
    queryFn: () => salesService.getAll(params),
  });
}

// ─── Inventory ───────────────────────────────────────────────────────────────
export function useInventory(params: { skip?: number; limit?: number; status?: string; warehouse?: string } = {}) {
  return useQuery({
    queryKey: ['inventory', params],
    queryFn: () => inventoryService.getAll(params),
  });
}

export function useInventoryAlerts() {
  return useQuery({
    queryKey: ['inventory-alerts'],
    queryFn: () => inventoryService.getAlerts(),
  });
}

export function useInventoryLowStock() {
  return useQuery({
    queryKey: ['inventory-low-stock'],
    queryFn: () => inventoryService.getLowStock(),
  });
}

export function useInventoryRecommendations() {
  return useQuery({
    queryKey: ['inventory-recommendations'],
    queryFn: () => inventoryService.getRecommendations(),
  });
}

export function useInventorySummary() {
  return useQuery({
    queryKey: ['inventory-summary'],
    queryFn: () => inventoryService.getSummary(),
  });
}

// ─── Forecast ────────────────────────────────────────────────────────────────
export function useDynamicForecast(productId: string) {
  return useQuery({
    queryKey: ['forecast-dynamic', productId],
    queryFn: () => forecastService.getDynamicForecast(productId),
    enabled: !!productId,
  });
}

export function useProductForecasts(productId: string) {
  return useQuery({
    queryKey: ['forecast-product', productId],
    queryFn: () => forecastService.getByProduct(productId),
    enabled: !!productId,
  });
}

// ─── Recommendations ─────────────────────────────────────────────────────────
export function useRecommendations(customerId: string, topN: number = 10) {
  return useQuery({
    queryKey: ['recommendations', customerId, topN],
    queryFn: () => recommendationService.getForCustomer(customerId, topN),
    enabled: !!customerId,
  });
}

// ─── Analytics ───────────────────────────────────────────────────────────────
export function useDashboard() {
  return useQuery({
    queryKey: ['analytics-dashboard'],
    queryFn: () => analyticsService.getDashboard(),
  });
}

export function useSalesAnalytics() {
  return useQuery({
    queryKey: ['analytics-sales'],
    queryFn: () => analyticsService.getSales(),
  });
}

export function useCustomerAnalytics() {
  return useQuery({
    queryKey: ['analytics-customers'],
    queryFn: () => analyticsService.getCustomers(),
  });
}

export function useInventoryAnalytics() {
  return useQuery({
    queryKey: ['analytics-inventory'],
    queryFn: () => analyticsService.getInventory(),
  });
}

// ─── Users ───────────────────────────────────────────────────────────────────
export function useUsers(params: { skip?: number; limit?: number } = {}) {
  return useQuery({
    queryKey: ['users', params],
    queryFn: () => userService.getAll(params),
  });
}
