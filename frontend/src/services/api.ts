/**
 * Centralized API configuration — Demand Sphere Frontend
 * ====================================================
 * Configures Axios with:
 * - Base URL from constants
 * - Automatic token injection for headers
 * - Timeout settings
 * - Standardized error mapping
 */

import axios from 'axios';
import { API_BASE_URL } from '../constants';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ─── Request Interceptor: Token Injection ────────────────────────────────────
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('demandsphere_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ─── Response Interceptor: Auth Failures & Logging ───────────────────────────
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const { status } = error.response;
      if (status === 401) {
        console.warn('[Auth] Token expired or invalid, signing out...');
        localStorage.removeItem('demandsphere_token');
        localStorage.removeItem('demandsphere_user');
        // If not already on login page, redirect
        if (!window.location.pathname.endsWith('/login')) {
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;
export const axiosInstance = api; // alias for flexible imports
